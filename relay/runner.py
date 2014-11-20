from __future__ import division
import argparse_tools as at
from collections import deque
import numpy as np
import os
from os.path import abspath, dirname, join
import subprocess
import time

from relay import log, configure_logging, add_zmq_log_handler
from relay import util


def start_webui():
    cwd = join(dirname(dirname(abspath(__file__))), 'web')
    log.info("Starting node.js webui in a subshell")
    subprocess.Popen(
        'cd %s ; node index.js' % cwd, shell=True,
        preexec_fn=os.setsid)  # guarantee that the child process exits with me


@util.coroutine
def window(n, initial_data=()):
    win = deque(initial_data, n)
    while 1:
        win.append((yield win))


def calc_weight(errdata):
    sp = np.fft.fft(errdata)[1: len(errdata) // 2]
    if sp.sum() == 0:  # there is no variation in the signal
        log.warn('no variation in the signal.  fft cannot continue')
        return 1

    # get the phase in radians  # -np.pi < phase <= +np.pi
    phase = np.angle(sp)  # radians

    # find the amplitude integral of neighboring samples.
    # search <360 degrees to left of most recent sample's phase
    # p_k = phase - degrees_between_samples * k  # kth phase
    amplitude_integrals = np.sin(phase)  # iteratively updated
    # samples per cycle
    kth = len(errdata) / np.arange(1, len(errdata) // 2)
    num_degrees_between_samples = 2 * np.pi / kth
    p_k = phase.copy()
    while (kth > 0).any():
        # find amplitude of a sign wave at specific phase
        p_k -= num_degrees_between_samples
        amplitude_integrals += np.abs(np.sin(p_k))
        kth -= 1
        idxs = kth > 0
        not_idxs = ~idxs
        kth = kth[idxs]
        p_k[not_idxs] = 0
        num_degrees_between_samples[not_idxs] = 0

    # get the amplitude of each frequency in the fft spectrum
    amplitude = np.abs(sp)

    return (
        (np.sin(phase) / amplitude_integrals)
        * (amplitude / amplitude.sum())
    ).sum()


def create_ramp_plan(err, ramp):
    """
    Formulate and execute on a plan to slowly add heat or cooling to the system

    `err` initial error (PV - SP)
    `ramp` the size of the ramp

    A ramp plan might yield MVs in this order at every timestep:
        [5, 0, 4, 0, 3, 0, 2, 0, 1]
        where err == 5 + 4 + 3 + 2 + 1
    """
    if ramp == 1:  # basecase
        yield err
        while True:
            yield 0
    # np.arange(n).sum() == err
    # --> solve for n
    # err = (n - 1) * (n // 2) == .5 * n**2 - .5 * n
    # 0 = n**2 - n - 2*err  --> solve for n
    n = np.abs(np.roots([.5, -.5, -err]).max())
    niter = int(ramp // (2 * n))  # 2 means add all MV in first half of ramp
    MV = n
    log.info('Initializing a ramp plan', extra=dict(
        ramp_size=ramp, err=err, niter=niter))
    for x in range(int(n)):
        budget = MV
        for x in range(niter):
            budget -= MV // niter
            yield int(np.sign(err) * (MV // niter))
        yield int(budget * np.sign(err))
        MV -= 1
    while True:
        yield 0


def main(ns):
    # logging... for some reason, the order in which you add handlers matters
    if ns.sendstats:
        if ns.sendstats == 'webui':
            add_zmq_log_handler('ipc:///tmp/relaylog')
        else:
            add_zmq_log_handler(ns.sendstats)
    configure_logging(True)
    log.info(
        "Starting relay!", extra={k: str(v) for k, v in ns.__dict__.items()})
    if ns.sendstats == 'webui':
        start_webui()

    metric = ns.metric()
    target = ns.target()
    errhist = window(ns.lookback)
    ramp_index = 0

    while True:
        SP = next(target)  # set point
        PV = next(metric)  # process variable
        err = (SP - PV)
        log.debug('got metric value', extra=dict(PV=PV, SP=SP))
        if ramp_index < ns.ramp:
            if ramp_index == 0:
                plan = create_ramp_plan(err, ns.ramp)
            ramp_index += 1
            MV = next(plan)
            errdata = errhist.send(0)
        else:
            errdata = errhist.send(err)
            weight = calc_weight(errdata)
            MV = int(err + -1 * weight * sum(errdata) / len(errdata))
            log.info('data', extra=dict(data=[
                err, weight,
                sum(errdata) / len(errdata)]))

        if MV > 0:
            if ns.warmer:
                log.debug('adding heat', extra=dict(MV=MV, err=err))
                ns.warmer(MV)
            else:
                log.warn('too cold')
        elif MV < 0:
            if ns.cooler:
                log.debug('removing heat', extra=dict(MV=MV, err=err))
                ns.cooler(MV)
            else:
                log.warn('too hot')
        else:
            log.debug(
                'stabilized PV at setpoint', extra=dict(MV=MV, PV=PV, SP=SP))
        time.sleep(ns.delay)


def targettype(x):
    try:
        _target = int(x)

        def infinite_iterator():
            return (_target for _ in iter(int, 1))
        return infinite_iterator
    except ValueError:
        return util.load_obj_from_path(x, prefix='relay.plugins')


build_arg_parser = at.build_arg_parser([
    at.add_argument(
        '-m', '--metric', required=True,
        default=os.environ.get('RELAY_METRIC'),
        type=lambda x: util.load_obj_from_path(x, prefix='relay.plugins'),
        help=(
            ' This should point to generator (function or class) that,'
            ' when called, returns a metric value.  In a PID controller, this'
            ' corresponds to the process variable (PV).'
            '  Valid examples:\n'
            '  "bash_echo_metric"'
            '  (this loads relay.plugins.bash_echo_metric),\n'
            '  "relay.plugins.bash_echo_metric",\n'
            '  "mycode.custom_metric"\n'
        )),
    at.add_argument(
        '-w', '--warmer', default=os.environ.get('RELAY_WARMER'),
        type=lambda x: util.load_obj_from_path(x, prefix='relay.plugins'),
        help=(
            ' This should point to a function that starts n additional tasks.'
            ' In a PID controller, this is the manipulated variable (MV).'
            '  Valid examples:\n'
            '  "bash_echo_warmer",\n'
            '  "relay.plugins.bash_echo_warmer",\n'
            '  "mycode.my_warmer_func"\n'
        )),
    at.add_argument(
        '-t', '--target',
        default=os.environ.get('RELAY_TARGET', targettype(0)),
        type=targettype, help=(
            "A target value that the metric we're watching should stabilize"
            " at."
            ' For instance, if relay is monitoring a queue size, the target'
            ' value is 0.  In a PID controller, this value corresponds'
            ' to the setpoint (SP).'
        )),
    at.add_argument(
        '-c', '--cooler', default=os.environ.get('RELAY_COOLER'),
        type=lambda x: util.load_obj_from_path(x, prefix='relay.plugins'),
        help=(
            ' This should point to a function or class that terminates n'
            " instances of your tasks."
            '  In a PID controller, this is the manipulated variable (MV).'
            " You may not want to implement"
            " both a warmer and a cooler.  Does your thermostat toggle"
            " the heating element and air conditioner at the same time?"
            " For valid examples, see the --warmer syntax"
        )),
    at.add_argument(
        '-d', '--delay', type=float, default=os.environ.get('RELAY_DELAY', 1),
        help='num seconds to wait between metric polling'),
    at.add_argument(
        '--sendstats', default=os.environ.get('RELAY_SENDSTATS'), help=(
            'You can visualize how well relay is'
            ' tuned to your particular metric with the stats generated.'
            ' If "--sendstats webui" passed, spin up a node.js webserver in a'
            ' subshell and pass to it the json log messages.'
            ' If any other argument is'
            ' passed, it must be a zmq uri that will'
            ' receive arbitrary json-encoded log messages from relay.'
        )),
    at.add_argument(
        '--lookback', default=os.environ.get('RELAY_LOOKBACK', 1000), type=int,
        help=(
            'Keep a history of the last n PV samples for online tuning')),
    at.add_argument(
        '--ramp', type=int, default=os.environ.get('RELAY_RAMP', 1), help=(
            'Add heat or cooling over the first n samples.  This is useful'
            ' if you do not want to add a lot of heat all at once')),
])

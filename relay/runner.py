from __future__ import division

from collections import deque
import numpy as np
import os
from os.path import abspath, dirname, join
import subprocess
import sys
import time
import threading

from relay import log, configure_logging, add_zmq_log_handler
from relay import util
from relay import argparse_shared as at


def start_webui():
    cwd = join(dirname(dirname(abspath(__file__))), 'web/src')
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
    amplitude_integrals = np.abs(np.sin(phase))  # iteratively updated
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
        # np.sin(phase)
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
        yield int(err)
        while True:
            yield 0
    # np.arange(n).sum() == err
    # --> solve for n
    # err = (n - 1) * (n // 2) == .5 * n**2 - .5 * n
    # 0 = n**2 - n  --> solve for n
    n = np.abs(np.roots([.5, -.5, 0]).max())
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


def validate_ns_or_sysexit(ns):
    ex = 0
    if None in [ns.target, ns.metric]:
        log.error("you must define a --metric and --target!")
        ex = 1
    if ns.warmer is None and ns.cooler is None:
        log.error("you must define either a --warmer or a --cooler!")
        ex = 1
    if ex:
        build_arg_parser().print_usage()
        sys.exit(1)


def evaluate_stop_condition(errdata, stop_condition):
    """
    Call the user-defined function: stop_condition(errdata)
    If the function returns -1, do nothing.  Otherwise, sys.exit.
    """
    if stop_condition:
        return_code = stop_condition(list(errdata))
        if return_code != -1:
            log.info(
                'Stop condition triggered!  Relay is terminating.',
                extra=dict(return_code=return_code))
            sys.exit(return_code)


def main(ns):
    validate_ns_or_sysexit(ns)
    configure_logging(True)
    if ns.sendstats:
        if ns.sendstats == 'webui':
            add_zmq_log_handler('ipc:///tmp/relaylog')
            start_webui()
        else:
            add_zmq_log_handler(ns.sendstats)
    log.info(
        "Starting relay!", extra={k: str(v) for k, v in ns.__dict__.items()})

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
            MV = int(round(err - weight * sum(errdata) / len(errdata)))
            log.info('data', extra=dict(data=[
                err, weight,
                sum(errdata) / len(errdata)]))

        if MV > 0:
            if ns.warmer:
                log.debug('adding heat', extra=dict(MV=MV, err=err))
                threading.Thread(target=ns.warmer, args=(MV,)).start()
            else:
                log.warn('too cold')
        elif MV < 0:
            if ns.cooler:
                log.debug('removing heat', extra=dict(MV=MV, err=err))
                threading.Thread(target=ns.cooler, args=(MV,)).start()
            else:
                log.warn('too hot')
        else:
            log.debug(
                'stabilized PV at setpoint', extra=dict(MV=MV, PV=PV, SP=SP))
        time.sleep(ns.delay)
        evaluate_stop_condition(list(errdata), ns.stop_condition)


build_arg_parser = at.build_arg_parser([
    at.group(
        "What is Relay optimizing?",
        at.metric, at.target),
    at.group(
        "Instruct Relay how to heat or cool your metric",
        at.warmer, at.cooler),
    at.group(
        "Some optional Relay parameters",
        at.delay, at.lookback, at.ramp, at.sendstats, at.stop_condition),
])

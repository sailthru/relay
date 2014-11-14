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


def main(ns):
    # logging... for some reason, the order in which you add handlers matters
    if ns.sendstats:
        if ns.sendstats == 'webui':
            add_zmq_log_handler('tcp://127.0.0.1:2001')
    configure_logging(True)
    log.info(
        "Starting relay!", extra={k: str(v) for k, v in ns.__dict__.items()})
    if ns.sendstats == 'webui':
        start_webui()

    metric = ns.metric()
    SP = ns.target  # set point
    err = 0
    pvhist = window(ns.lookback)
    maxweight = float('-inf')

    while True:
        PV = next(metric)  # process variable
        pvdata = pvhist.send(PV)
        if len(pvdata) > 50:
            sp = np.fft.fft(pvdata)[:len(pvdata) / 2]

            # get the phase in degrees.
            # then shift phase of each wavelength by half a period
            # ie make a mirror image of a sin wave about the x axis
            # use 0 to 360 rather than -180 to +180 degrees
            phase = (np.angle(sp, True) + 180)
            phase = (phase + 180) % 360
            # instead of above, can I just do 180 + np.angle(sp, True) * -1

            # TODO: get this to work
            # find the integral of neighboring samples.
            # search up to 1/2 wavelength to right and 1/2 wavelength to left
            # from current phase
            freqs = np.arange(0, len(pvdata) / 2 - 1) / (ns.delay * len(pvdata))
            # phase difference between samples
            # print freqs[0:2]
            degrees_per_sample = (1 / freqs) * ns.delay
            degrees_per_sample = (
                np.arange(0, len(pvdata) / 2 - 1) * ns.delay * ns.delay
                * len(pvdata))
            # TODO: pretty sure this is wrong
            # num degrees per sample in 1/2 the wavelength
            num_neighbors = freqs / degrees_per_sample / 2
            num_neighbors[np.isnan(num_neighbors)] = 0

            # TODO: test that the below calculates the integral properly
            phase_window_integrals = np.zeros(phase.size)
            while num_neighbors[num_neighbors > 0].sum() > 1:
                # TODO: this is incorrect until   += amplitude_at(...)
                phase_window_integrals += (
                    phase + num_neighbors * degrees_per_sample) % 360
                phase_window_integrals += (
                    phase - num_neighbors * degrees_per_sample) % 360
                num_neighbors[num_neighbors >= 1] -= 1

            # get the amplitude of each frequency in the fft spectrum
            amplitude = np.abs(sp)
            weight = (
                phase / phase_window_integrals
                * amplitude / amplitude.sum()
            ).sum()

            # bound weight so it's less than and potentially close to 1
            if weight > maxweight:
                maxweight = weight
            else:
                weight = weight / maxweight
            # TODO: maxweight is a hack.  find a real bound
            print weight
        else:
            weight = 1
        log.debug('got metric value', extra=dict(PV=PV))
        err = (SP - PV)

        MV = int(err * weight)  # int(MV / 2)

        if MV <= 0:
            continue
        if MV > 0:
            if ns.warmer:
                log.debug('adding heat', extra=dict(MV=MV, err=err))
                ns.warmer(MV)
            else:
                log.warn('too cold', extra=dict(MV=+0, err=err))
        elif MV < 0:
            if ns.cooler:
                log.debug('removing heat', extra=dict(MV=MV, err=err))
                ns.cooler(MV)
            else:
                log.warn('too hot', extra=dict(MV=-0, err=err))
        else:
            log.debug(
                'stabilized PV at setpoint', extra=dict(MV=MV, PV=PV))
        time.sleep(ns.delay)


build_arg_parser = at.build_arg_parser([
    at.add_argument(
        '-m', '--metric', required=True,
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
        '-w', '--warmer',
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
        '-t', '--target', default=0, type=int, help=(
            "A target value that the metric we're watching should stabilize at."
            ' For instance, if relay is monitoring a queue size, the target'
            ' value is 0.  In a PID controller, this value corresponds'
            ' to the setpoint (SP).'
        )),
    at.add_argument(
        '-c', '--cooler',
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
        '--sendstats', help=(
            'You can visualize how well relay is'
            ' tuned to your particular metric with the stats generated.'
            ' If "--sendstats webui" passed, spin up a node.js webserver in a'
            ' subshell and pass to it the json log messages.'
            ' If any other argument is'
            ' passed, it must be a zmq uri that will'
            ' receive arbitrary json-encoded log messages from relay.'
        )),
    at.add_argument(
        '--lookback', default=1000, type=int, help=(
            'Keep a history of the last n PV samples for online tuning'))
])

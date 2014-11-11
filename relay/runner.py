from __future__ import division
import argparse_tools as at
from collections import deque
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
def window(n, initial_data=None):
    if initial_data:
        win = deque(initial_data, n)
    else:
        win = deque(((yield) for _ in range(n)), n)
    while 1:
        win.append((yield win))

import numpy as np

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
    Kp = 1  # adjustment on error to ramp up slower (0<Kp<1) or faster (Kp>1)
    pvwindow = window(ns.lookback)
    [pvwindow.send(0) for _ in range(ns.lookback)]

    while True:
        PV = next(metric)  # process variable
        log.debug('got metric value', extra=dict(PV=PV))
        err = (SP - PV)

        hist = pvwindow.send(err)
        # do something with this!
        MV = err * Kp
        if MV > 0:
            if ns.warmer:
                log.debug('adding heat', extra=dict(MV=MV, err=err))
                ns.warmer(MV - abs(integral))
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
        '--lookback', default=100, type=int, help=(
            'Keep a history of the last n PV samples for online tuning'))
])

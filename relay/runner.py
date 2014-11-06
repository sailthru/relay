from __future__ import division
import argparse_tools as at
import os
import time

from relay import log, configure_logging
from relay import util

configure_logging(True)


def main(ns):
    log.info("Starting relay!", extra=dict(**ns.__dict__))
    metric = ns.metric()
    SP = ns.target  # set point
    err = 0
    Kp = 1  # adjustment on error to ramp up slower (0<Kp<1) or faster (Kp>1)
    while True:
        PV = next(metric)  # process variable
        log.debug('got metric value', extra=dict(PV=PV))
        err = (SP - PV)
        MV = err * Kp

        if MV > 0:
            if ns.warmer:
                log.debug('adding heat', extra=dict(MV=MV, err=err))
                ns.warmer(MV)
            else:
                log.warn('too cold', extra=dict(err=err))
        elif MV < 0:
            if ns.cooler:
                log.debug('removing heat', extra=dict(MV=MV, err=err))
                ns.cooler(MV)
            else:
                log.warn('too hot', extra=dict(err=err))
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
            '  "Always1"  (this loads relay.metrics.Always1),\n'
            '  "relay.metrics.Always1",\n'
            '  "mycode.custom_metric.plugin"\n'
        )),
    at.add_argument(
        '-w', '--warmer',
        type=lambda x: util.load_obj_from_path(x, prefix='relay.plugins'),
        help=(
            ' This should point to a function that starts n additional tasks.'
            ' In a PID controller, this is the manipulated variable (MV).'
            '  Valid examples:\n'
            '  "bash_echo",\n'
            '  "relay.warmers.bash_echo",\n'
            '  "mycode.custom_warmer.plugin"\n'
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
        )),
    at.add_argument(
        '--delay', type=float, default=os.environ.get('RELAY_DELAY', 1),
        help='num seconds to wait between metric polling'),
])

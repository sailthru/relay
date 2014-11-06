import argparse_tools as at
import os
import time

from relay import log, configure_logging
from relay import util

configure_logging(True)


def main(ns):
    log.info("Starting relay!", extra=dict(**ns.__dict__))
    metric = ns.metric()
    # Implement the PID algorithm
    # TODO: finish
    SP = ns.target
    while True:
        PV = next(metric)
        log.debug('got metric value', extra=dict(PV=PV))
        if PV < SP:
            if ns.warmer:
                n = SP - PV
                log.debug('adding heat', extra=dict(MV=n))
                ns.warmer(n)
            else:
                log.warn('too cold', extra=dict(PV=PV))
        elif PV > SP:
            if ns.cooler:
                n = PV - SP
                log.debug('removing heat', extra=dict(MV=n * -1))
                ns.cooler(n)
            else:
                log.warn('too hot', extra=dict(PV=PV))
        else:
            log.debug('stabilized at setpoint',
                      extra=dict(stabilized_value=ns.target))
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

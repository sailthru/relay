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
        if (PV - SP) > 0:
            ns.launcher(1)
        time.sleep(ns.delay)


build_arg_parser = at.build_arg_parser([
    at.add_argument(
        '-m', '--metric', required=True,
        type=lambda x: util.load_obj_from_path(x, prefix='relay.metrics'),
        help=(
            'Please supply the name of a supported relay metric plugin or'
            ' a python import path that will load your own custom plugin. '
            ' This should point to generator (function or class) that,'
            ' when called, returns a metric value.  In a PID controller, this'
            ' corresponds to the process variable (PV).'
            '  Valid examples:\n'
            '  "Always1"  (this loads relay.metrics.Always1),\n'
            '  "relay.metrics.Always1",\n'
            '  "mycode.custom_metric.plugin"\n'
        )),
    at.add_argument(
        '-l', '--launcher', required=True,
        type=lambda x: util.load_obj_from_path(x, prefix='relay.launchers'),
        help=(
            'Please supply the name of a supported relay launcher plugin or'
            ' a python import path that will load your own custom plugin. '
            ' This should point to a function that executes your task.  In a'
            ' PID controller, this corresponds to the manipulated variable (MV)'
            '  Valid examples:\n'
            '  "bash_echo",\n'
            '  "relay.launchers.bash_echo",\n'
            '  "mycode.custom_launcher.plugin"\n'
        )),
    at.add_argument(
        '-t', '--target', default=0, type=int, help=(
            "A target value that the metric we're watching should stabilize at."
            ' For instance, if relay is monitoring a queue size, the target'
            ' value is 0.  In a PID controller, this value corresponds'
            ' to the setpoint (SP).'
        )),
    at.add_argument(
        '--delay', type=int, default=os.environ.get('RELAY_DELAY', 1),
        help='num seconds to wait between metric polling'),
])

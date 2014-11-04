import argparse_tools as at
import os
import time

from relay import log, configure_logging
from relay import util

configure_logging(True)


def main(ns):
    log.info("Starting relay!", extra=dict(**ns.__dict__))
    metric = ns.metric()
    while True:
        if next(metric) > 0:
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
            ' when called, returns a metric value.'
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
            ' This should point to a function or class that ....'  # TODO
            '  Valid examples:\n'
            '  "bash_echo",\n'
            '  "relay.launchers.bash_echo",\n'
            '  "mycode.custom_launcher.plugin"\n'
        )),
    at.add_argument(
        '--delay', type=int, default=os.environ.get('RELAY_DELAY', 1),
        help='num seconds to wait between metric polling'),
])

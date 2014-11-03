import argparse_tools as at

from relay import log, configure_logging
from relay import util

configure_logging(True)


def main(ns):
    log.info("Starting relay!", extra=dict(**ns.__dict__))


build_arg_parser = at.build_arg_parser([
    at.add_argument(
        '-m', '--metric_plugin', required=True,
        type=lambda x: util.load_obj_from_path(x, prefix='relay.metrics'),
        help=(
            'Please supply the name of a supported relay metric plugin or'
            'a python import path that will load your own custom plugin.'
            '  Valid examples:\n'
            '  Always1  (this loads relay.metrics.Always1)\n'
            '  relay.metrics.Always1\n'
            '  mycode.custom_metric.plugin\n'
        )),
    at.add_argument(
        '-l', '--launcher_plugin', required=True,
        type=lambda x: util.load_obj_from_path(x, prefix='relay.launchers'),
        help=(
            'Please supply the name of a supported relay launcher plugin or'
            'a python import path that will load your own custom plugin.'
            '  Valid examples:\n'
            '  bash_echo\n'
            '  relay.metrics.bash_echo\n'
            '  mycode.custom_launcher.plugin\n'
        )),
])

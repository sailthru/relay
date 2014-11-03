import argparse_tools as at

from relay import log, configure_logging


def main(ns):
    configure_logging(True)
    log.info("Starting relay!", extra=dict(**ns.__dict__))


build_arg_parser = at.build_arg_parser([
    at.add_argument(
        '-m', '--metric_plugin', required=True,
        type=lambda x: x, #util.load_obj_from_path(x, prefix='relay.metrics'),
        help=(
            'Please supply the name of a supported relay metric plugin or'
            'a python import path that will load your own custom plugin.'
            '  Valid examples:\n'
            '  relay.metrics.Always1\n'
            '  Always1  (this loads relay.metrics.Always1)\n'
            '  mycode.custom_metric.plugin\n'
        )),
])

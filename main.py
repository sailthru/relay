import argparse_tools as at

from relay import log
from relay import util


def main(ns):
    log.info("Starting relay!", extra=dict(**ns.__dict__))
    pass


def load_metric_plugin(metric_plugin_path):
    """
    Attempt to load a relay metric plugin instance from an import path

    `metric_plugin_path` a python import path pointing to a plugin object.
        Example:
            metric_plugin_path='zookeeper'
            metric_plugin_path='relay.metrics.zookeeper'
            metric_plugin_path='mycode.custom_metric.plugin'


    """
    if metric_plugin_path.startswith('relay.metrics'):
        return util.load_obj_from_path(metric_plugin_path)
    else:
        try:
            return util.load_obj_from_path(
                'relay.metrics.%s' % metric_plugin_path)
        except ImportError:
            return util.load_obj_from_path(metric_plugin_path)


at.build_arg_parser([
    at.add_argument(
        '-m', '--metric_plugin', required=True, help=(
            'Please supply the name of a supported relay metric plugin or'
            'a python import path that will load your own custom plugin.'
            '  An example path is relay.metrics.zookeeper'
        )),
])

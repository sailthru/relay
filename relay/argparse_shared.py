"""
Define Relay's argparse options here so that external code that calls Relay
may choose to safely override or inherit the default options

This module defines all inputs that Relay supports
"""
from argparse_tools import (
    lazy_kwargs, build_arg_parser, group, add_argument_default_from_env_factory)

from relay import util

# expose argparse_tools code
build_arg_parser
group
add_argument = add_argument_default_from_env_factory(env_prefix='RELAY_')


@lazy_kwargs
def metric(
    parser,
    type=lambda x: util.load_obj_from_path(x, prefix='relay.plugins'),
    help=(
        ' This should point to generator (function or class) that,'
        ' when called, returns a metric value.  In a PID controller, this'
        ' corresponds to the process variable (PV).  Warming the system'
        ' should eventually increase metric values and cooling should'
        ' decrease them. '
        '  Valid examples:\n'
        '  "bash_echo_metric"'
        '  (this loads relay.plugins.bash_echo_metric),\n'
        '  "relay.plugins.bash_echo_metric",\n'
        '  "mycode.custom_metric"\n')):
    add_argument('-m', '--metric', type=type, help=help)(parser)


def targettype(x):
    try:
        _target = int(x)

        def infinite_iterator():
            return (_target for _ in iter(int, 1))
        return infinite_iterator
    except ValueError:
        return util.load_obj_from_path(x, prefix='relay.plugins')


@lazy_kwargs
def target(
    parser,
    type=targettype,
    help=(
        "A target value that the metric we're watching should stabilize"
        " at."
        ' For instance, if relay is monitoring a queue size, the target'
        ' value is 0.  In a PID controller, this value corresponds'
        ' to the setpoint (SP).')):
    add_argument('-t', '--target', type=type, help=help)(parser)


@lazy_kwargs
def warmer(
    parser,
    type=lambda x: util.load_obj_from_path(x, prefix='relay.plugins'),
    help=(
        ' This should point to a function that starts n additional tasks.'
        ' In a PID controller, this is the manipulated variable (MV).'
        '  Valid examples:\n'
        '  "bash_echo_warmer",\n'
        '  "relay.plugins.bash_echo_warmer",\n'
        '  "mycode.my_warmer_func"\n')):
    add_argument('-w', '--warmer', type=type, help=help)(parser)


@lazy_kwargs
def cooler(
    parser,
    type=lambda x: util.load_obj_from_path(x, prefix='relay.plugins'),
    help=(
        ' This should point to a function or class that terminates n'
        " instances of your tasks."
        '  In a PID controller, this is the manipulated variable (MV).'
        " You may not want to implement"
        " both a warmer and a cooler.  Does your thermostat toggle"
        " the heating element and air conditioner at the same time?"
        " For valid examples, see the --warmer syntax")):
    add_argument('-c', '--cooler', type=type, help=help)(parser)


@lazy_kwargs
def delay(parser, default=1):
    add_argument(
        '-d', '--delay', type=float, default=default,
        help='num seconds to wait between metric polling. ie. 1/sample_rate'
    )(parser)


@lazy_kwargs
def sendstats(parser):
    add_argument(
        '--sendstats', help=(
            'You can visualize how well relay is'
            ' tuned to your particular metric with the stats generated.'
            ' If "--sendstats webui" passed, spin up a node.js webserver in a'
            ' subshell and pass to it the json log messages.'
            ' If any other argument is'
            ' passed, it must be a zmq uri that will'
            ' receive arbitrary json-encoded log messages from relay.'
        ))(parser)


@lazy_kwargs
def lookback(parser, default=1000):
    add_argument(
        '--lookback', default=default, type=int,
        help=(
            'Keep a history of the last n PV samples for online tuning')
    )(parser)


@lazy_kwargs
def ramp(parser, default=1):
    add_argument(
        '--ramp', type=int, default=default, help=(
            'Add heat or cooling over the first n samples.  This is useful'
            ' if you do not want to add a lot of heat all at once')
    )(parser)


@lazy_kwargs
def stop_condition(parser):
    add_argument(
        '--stop_condition',
        type=lambda x: util.load_obj_from_path(x, prefix='relay.plugins'),
        help=(
            'Optional.  This should point to a function that examines the'
            ' error history and determines whether Relay should exit. The'
            ' return code returned by this function gets passed to'
            ' sys.exit(...)'
            '  Valid examples:\n'
            '  "stop_if_mostly_diverging",\n'
            '  "mycode.my_stop_condition"\n')
    )(parser)

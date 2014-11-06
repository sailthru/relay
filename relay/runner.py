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
    # Implement the PID algorithm
    # http://www.scribd.com/doc/19070283/Discrete-PI-and-PID-Controller-Design-and-Analysis-for-Digital-Implementation
    SP = ns.target  # set point
    MV = 0  # measure value
    err = prev_err = 0
    integral = 0  # ideal
    total_err = 0  # positional, incremental
    Kp, Ti, Td = [1, 10, .001]
    data = []  # debug
    MV1 = MV2 = 0  # debug
    # while True:
    while len(data) < 100:
        PV = next(metric)
        prev_prev_err = prev_err
        prev_err = err
        err = (SP - PV)

        # PID ideal form
        Ki = Kp / Ti
        Kd = Kp * Td
        derivative = (err - prev_err) / ns.delay
        integral += err * ns.delay
        MV3 = Kp * err + Ki * integral + Kd * derivative

        # positional PID algorithm
        total_err += err
        MV2 = Kp * (err + ns.delay / Ti * total_err)

        # incremental PI algorithm
        MV_delta = Kp * (err - prev_err) * (1 + ns.delay / Ti)
        MV1 = MV1 + Kp * (err - prev_err) * (1 + ns.delay / Ti)

        # velocity PID algorithm
        MV = Kp * (
            err * (1 + ns.delay / Ti + Td / ns.delay)
            + prev_err * (-1 - 2 * Td / ns.delay)
            + Td / ns.delay * prev_prev_err)

        # debug
        print MV, MV1, MV2, MV3
        data.append((MV, MV1, MV2, MV3))

        ns.warmer(1)
        log.debug('got metric value', extra=dict(PV=PV))
        if MV < .5:
            if ns.warmer:
                log.debug('adding heat', extra=dict(MV=MV))
                ns.warmer(int(MV))
            else:
                log.warn('too cold', extra=dict(MV=MV))
        elif MV > .5:
            if ns.cooler:
                log.debug('removing heat', extra=dict(MV=MV))
                ns.cooler(abs(int(MV)))
            else:
                log.warn('too hot', extra=dict(MV=MV))
        else:
            log.debug('stabilized PV at setpoint', extra=dict(MV=MV, PV=PV))
        time.sleep(ns.delay)
    import pandas as pd
    df = pd.DataFrame(data)
    # pylab
    # figure()
    # plot(df[0])
    # plot(df[1])
    # plot(df[2])
    # plot(df[3])
    import IPython ; IPython.embed()


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

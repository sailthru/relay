"""
Metrics are generators that Relay can use to determine whether it's an
appropriate time to execute your task
"""
import collections


class MetricPluginInterface(collections.Iterator):
    """
    Base class that all metric plugins can inherit from.  A plugin is just an
    iterator, so you can also define function generators that have the
    same effect.
    """
    def __init__(self, config):
        pass  # do nothing with config

    def __next__(self):
        """Return an integer number"""
        raise NotImplementedError()


class Always1(object):
    """An example metric that always returns 1"""
    def __next__(self):
        return 1


def sometimes_1(_):
    import random
    while 1:
        yield random.choice([0, 1])


def square_wave_metric(_):
    """An example metric that oscillates between 0 and 1.
    This demos another way to design metric plugins using generators rather
    than classes"""
    n = 0
    while 1:
        n += 1
        if n % 8 < 4:
            yield 0

            # cap the size of the counter
            if n % 8 == 0:
                n = 0
        else:
            yield 1

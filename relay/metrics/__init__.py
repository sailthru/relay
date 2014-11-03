import collections


class PluginInterface(collections.Iterator):
    """
    Base class that all plugins can inherit from.  A plugin is just an
    iterator, so you can also define function generators that have the
    same effect.
    """
    def next(self):
        """Return an integer number"""
        raise NotImplementedError()


class Always1(collections.Iterator):
    """An example metric that always returns 1"""
    def next(self):
        return 1


def square_wave_metric():
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

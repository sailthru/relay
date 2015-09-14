"""
Relay plugins define 3 control points that relay can use:

    metrics - are generator functions that return values
    warmers - are functions that increase the value of the metric
    coolers - are functions that decrease the value of the metric

In a distributed environment, Relay may help you to:

    - autoscale the number of workers who are consuming from a queue
    - ensure there are enough concurrent processes running at any given time
    - generally stabilize a stream of numbers by functions that control
      increasing the values in the stream and decreasing the values in
      the stream

"""


def warmer(n):
    """A function that will increase values in your metric"""
    raise NotImplementedError()


def cooler(n):
    """A function that will decrease values in your metric"""
    raise NotImplementedError()


def metric():
    """A metric is a number stream that Relay polls every so often.
    Relay implicitly modifies this number stream when it calls the
    warmer() and cooler() functions.
    Relay attempts to minimize the difference between the current metric
    value and your current target value.

    This function could, for instance, yield the current temperature

    This function should be a generator.
    """
    while True:
        yield 0


def target():
    """
    A target is a number stream that Relay polls every so often.
    It defines a goal you'd like your metric to reach.
    Relay attempts to minimize the difference between the current metric
    value and your current target value.
    """
    while True:
        yield 0


def stop_condition(errdata):
    """A stop condition is an optional function that
    determines whether Relay should exit.

    The input is an array of the error history between the target and metric.
    The output is -1 or an integer return code that gets passed to sys.exit(...)
      You should return -1 as long as you want Relay to continue operating
    """
    return -1


######
# Example
#####


def oscillating_setpoint(_square_wave=False, shift=0):
    """A basic example of a target that you may want to approximate.

    If you have a thermostat, this is a temperature setting.
    This target can't change too often
    """
    import math
    c = 0
    while 1:
        if _square_wave:
            yield ((c % 300) < 150) * 30 + 20
            c += 1
        else:
            yield 10 * math.sin(2 * 3.1415926 * c + shift) \
                + 20 + 5 * math.sin(2 * 3.1415926 * c * 3 + shift)
            c += .001


def sinwave_setpoint():
    import math
    c = 0
    while 1:
        yield 60 + 50 * math.sin(c * 2 * math.pi)
        c += .005


def squarewave_setpoint():
    return oscillating_setpoint(True)


def bash_echo_metric():
    """A very basic example that monitors
    a number of currently running processes"""
    import subprocess
    # import random

    # more predictable version of the metric
    cmd = (
        'set -o pipefail '
        ' ; pgrep -f "^bash.*sleep .*from bash: started relay launcher"'
        ' | wc -l '
    )

    # less predictable version of the metric
    # cmd = 'ps aux|wc -l'

    while True:
        yield (
            int(subprocess.check_output(cmd, shell=True, executable='bash'))
            # + random.choice([-2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8])
        )


def bash_echo_warmer(n):
    """A very basic example of how to create n additional tasks.
    This is a warmer function with randomly delayed effects on the
    bash_echo_metric and random task lengths to make the metric less
    predictable
    """
    import subprocess
    import random
    cmd = (
        'set -o pipefail '
        " ; sleep %s "
        " ; sh -c 'echo from bash: started relay launcher task && sleep %s'"
    )
    for i in range(n):
        subprocess.Popen(
            cmd % ((1 + random.random()) * 1, (1 + random.random()) * 4),
            shell=True, stdout=subprocess.PIPE, executable='bash')


def bash_echo_cooler(n):
    """A very basic example of how to destroy n running tasks
    This is a cooler function
    """
    import subprocess
    cmd = (
        'set -o pipefile '
        ' ; kill `pgrep -f "from bash: started relay launcher task"'
        ' | tail -n %s` 2>/dev/null' % n)
    subprocess.Popen(cmd, shell=True, executable='bash').wait()


def stop_if_mostly_diverging(errdata):
    """This is an example stop condition that asks Relay to quit if
    the error difference between consecutive samples is increasing more than
    half of the time.

    It's quite sensitive and designed for the demo, so you probably shouldn't
    use this is a production setting
    """
    n_increases = sum([
        abs(y) - abs(x) > 0 for x, y in zip(errdata, errdata[1:])])
    if len(errdata) * 0.5 < n_increases:
        # most of the time, the next sample is worse than the previous sample
        # relay is not healthy
        return 0
    else:
        # most of the time, the next sample is better than the previous sample
        # realy is in a healthy state
        return -1

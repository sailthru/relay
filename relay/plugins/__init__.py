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
    """A generator function that represents some timeseries.
    For instance this function could yield the current temperature"""
    while True:
        yield 0


######
# Example
#####


def bash_echo_metric():
    """A very basic example that monitors
    a number of currently running processes"""
    import subprocess
    import random

    # more predictable version of the metric
    cmd = 'pgrep -f "from bash: started relay launcher" |wc -l'

    # less predictable version of the metric
    # cmd = 'ps aux|wc -l'

    while True:
        yield (
            int(subprocess.check_output(cmd, shell=True))
            # + random.choice([-2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8])
        )


def bash_echo_warmer(n):
    """A very basic example of how to create n additional tasks.
    This is a warmer function with randomly delayed effects on the
    bash_echo_metric and random task lengths to make the metric less predictable

    """
    import subprocess
    import random
    cmd = (
        "sleep %s "
        " ; sh -c 'echo from bash: started relay launcher task && sleep %s'"
    )
    for i in range(n):
        subprocess.Popen(
            cmd % ((1 + random.random()) ** 0, (1 + random.random() ** 0)),
            shell=True, stdout=subprocess.PIPE)


def bash_echo_cooler(n):
    """A very basic example of how to destroy n running tasks
    This is a cooler function
    """
    import subprocess
    cmd = (
        'kill `pgrep -f "from bash: started relay launcher task"'
        ' |tail -n %s` 2>/dev/null' % n)
    subprocess.Popen(cmd, shell=True).wait()

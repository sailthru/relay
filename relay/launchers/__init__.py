"""
Launchers are functions that Relay can use to execute your task.
They are called when Relay believes launching more tasks will bring the metric
it is monitoring closer to the target value it is optimizing for.
"""


def launch(self, n):
    """Launch n tasks"""
    raise NotImplementedError()


def bash_echo_example(n):
    """A very basic example"""
    import subprocess
    cmd = 'echo from bash: started relay launcher task && sleep 2'
    for i in range(n):
        subprocess.Popen(cmd, shell=True)

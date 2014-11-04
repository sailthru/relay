"""
Launchers are functions that Relay can use to execute your task.
They are called when Relay believes launching more tasks will bring the metric
it is monitoring closer to the target value it is optimizing for.
"""
def launch(self):
    """Launch a task"""
    raise NotImplementedError()


def bash_echo_example():
    """A very basic example"""
    import subprocess
    cmd = 'echo from bash: started relay launcher task && sleep 2'
    subprocess.Popen(cmd, shell=True)

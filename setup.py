from distutils.core import setup
try:
    from setuptools import find_packages
except ImportError:
    print ("Please install Distutils and setuptools"
           " before installing this package")
    raise

setup(
    name='Relay',
    version='0.0.1',
    description=(
        'Run an arbitrary bash command as a mesos framework.'
        ' Scale up number of concurrently running instances based on a metric.'
        ' Generally good for auto-scaling workers.  Very similar to Marathon,'
        ' but designed for applications that quit or fail often.'
    ),
    long_description="Check the project homepage for details",
    keywords=['mesos', 'marathon', 'relay', 'framework'],

    author='Alex Gaudio',
    author_email='adgaudio@gmail.com',
    url='http://github.com/sailthru/relay',

    packages=find_packages(),
    include_package_data=True,
    install_requires=['argparse_tools', 'colorlog'],

    extras_require={
        'webui': ['pyzmq'],
        'mesos': ['mesos.native', 'mesos.cli', 'mesos.interface'],
    },
    tests_require=['nose'],
    test_suite="nose.main",
)

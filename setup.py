from distutils.core import setup
try:
    from setuptools import find_packages
except ImportError:
    print ("Please install Distutils and setuptools"
           " before installing this package")
    raise

setup(
    name='relay.runner',
    version='0.1.9',
    description=(
        'A smart thermostat.  Given a metric, or some timeseries that should'
        ' approach a given target, add heat or coolant as necessary'
        ' You can use Relay to auto-scale workers in large'
        ' distributed systems or do anything a thermostat might do.'
    ),
    long_description="Check the project homepage for details",
    keywords=[
        'relay', 'pid', 'pid controller', 'thermostat', 'tuning',
        'oscilloscope', 'auto-scale'],

    author='Alex Gaudio',
    author_email='adgaudio@gmail.com',
    url='http://github.com/sailthru/relay',

    packages=find_packages(),
    include_package_data=True,
    install_requires=['argparse_tools>=1.0.6', 'colorlog', 'numpy'],

    extras_require={
        'webui': ['pyzmq'],
    },
    tests_require=['nose'],
    test_suite="nose.main",
    zip_safe=True,

    entry_points = {
        'console_scripts': [
            'relay = relay.__main__:go',
        ],
        'setuptools.installation': [
            'eggsecutable = relay.__main__:go',
        ],
    },
)

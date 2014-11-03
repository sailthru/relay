import logging
log = logging.getLogger('relay')

# expose configure_logging to those who wish to develop relay
from relay.relay_logging import configure_logging

import os.path as _p
import pkg_resources as _pkg_resources
__version__ = _pkg_resources.get_distribution(
    _p.basename(_p.dirname(_p.abspath(__file__)))).version

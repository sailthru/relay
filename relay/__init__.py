import logging
log = logging.getLogger('relay.runner')

# expose configure_logging to those who wish to develop relay
from relay.relay_logging import configure_logging, add_zmq_log_handler

import pkg_resources as _pkg_resources
__version__ = _pkg_resources.get_distribution('relay.runner').version

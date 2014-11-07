import gevent.monkey
gevent.monkey.patch_all()

import logging
logging.basicConfig(level=logging.DEBUG)

from socketio.server import SocketIOServer
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import BroadcastMixin
import random


class PVData(BaseNamespace, BroadcastMixin):
    def recv_connect(self):
        def send():
            while True:
                vals = random.random() * 100
                self.emit('pvdata', {'y': vals})
                gevent.sleep(0.1)
        self.spawn(send)


class Application(object):
    def __init__(self):
        pass

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO'].rstrip('/')
        if path.startswith("socket.io"):
            socketio_manage(environ, {'/': PVData})


SocketIOServer(
    ('localhost', 8081), Application(), resource='socket.io',
    policy_server=True, policy_listener=('0.0.0.0', 10843)
).serve_forever()

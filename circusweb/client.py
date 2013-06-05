# -*- coding: utf-8 -
import uuid

import zmq
from zmq.utils.jsonapi import jsonmod as json
from zmq.eventloop.zmqstream import ZMQStream

from circus.exc import CallError
from circus.py3compat import string_types
from circus.util import DEFAULT_ENDPOINT_DEALER, get_connection
from circus.client import CircusClient


class AsynchronousCircusClient(CircusClient):
    """
    An asynchronous circus client implementation designed to works with tornado
    IOLoop
    """
    def __init__(self, loop, recv_callback, context=None,
                 endpoint=DEFAULT_ENDPOINT_DEALER, timeout=5.0,
                 ssh_server=None, ssh_keyfile=None):
        self.context = context or zmq.Context.instance()
        self.endpoint = endpoint
        self._id = uuid.uuid4().hex
        self.ssh_server = ssh_server
        self.ssh_keyfile = ssh_keyfile
        self._timeout = timeout
        self.timeout = timeout * 1000
        self.loop = loop
        self.recv_callback = recv_callback
        self.stream = ZMQStream(self.socket, self.loop)

    def call(self, cmd, callback):
        if not isinstance(cmd, string_types):
            try:
                cmd = json.dumps(cmd)
            except ValueError as e:
                raise CallError(str(e))

        socket = self.context.socket(zmq.DEALER)
        socket.setsockopt(zmq.IDENTITY, self._id)
        socket.setsockopt(zmq.LINGER, 0)
        get_connection(socket, self.endpoint, self.ssh_server,
                       self.ssh_keyfile)

        stream = ZMQStream(socket)
        stream.on_recv(lambda msg: callback(json.loads(msg)))

        try:
            self.socket.send(cmd)
        except zmq.ZMQError, e:
            raise CallError(str(e))

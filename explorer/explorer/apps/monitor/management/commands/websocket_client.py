import logging
from tornado import escape
from tornado import gen
from tornado import httpclient
from tornado import httputil
from tornado import ioloop
from tornado import websocket

import functools
import json
import time

__author__ = 'xiawu@xiawu.org'
__version__ = '$Rev$'
__doc__ = """   The abstract of web socket client """

logger = logging.getLogger(__name__)

APPLICATION_JSON = 'application/json'

DEFAULT_CONNECT_TIMEOUT = 60
DEFAULT_REQUEST_TIMEOUT = 60

 
class WebSocketClient(object):
    """Base for web socket clients.
    """
 
    def __init__(self, connect_timeout=DEFAULT_CONNECT_TIMEOUT,
                 request_timeout=DEFAULT_REQUEST_TIMEOUT):

        self.connect_timeout = connect_timeout
        self.request_timeout = request_timeout
        self._ws_connection = None

    def connect(self, url):
        """Connect to the server.
        :param str url: server URL.
        """
        websocket.websocket_connect(url, callback=self._connect_callback, on_message_callback=self._on_message)

    def send(self, data):
        """Send message to the server
        :param str data: message.
        """
        if not self._ws_connection:
            raise RuntimeError('Web socket connection is closed.')
        json_string = json.dumps(data,default=lambda obj:obj.__dict__)
        self._ws_connection.write_message(json_string, binary=True)

    def close(self):
        """Close connection.
        """

        if not self._ws_connection:
            raise RuntimeError('Web socket connection is already closed.')

        self._ws_connection.close()

    def _connect_callback(self, future):
        if future.exception() is None:
            self._ws_connection = future.result()
            self._on_connection_success()
            self.position = 1
            #self._read_messages()
        else:
            self._on_connection_error(future.exception())

    def _read_messages(self):
        self._ws_connection.read_message(callback=self._on_message)

    def _on_message(self, future):
        """This is called when new message is available from the server.
        :param str msg: server message.
        """

        pass

    def _on_connection_success(self):
        """This is called on successful connection ot the server.
        """

        pass

    def _on_connection_close(self):
        """This is called when server closed the connection.
        """
        pass

    def _on_connection_error(self, exception):
        """This is called in case if connection to the server could
        not established.
        """

        pass

"""The command implemenation of monitor blockchain

"""

__copyright__ = """ Copyright (c) 2016 Beijing ShenJiangHuDong Technology Co., Ltd. All rights reserved."""
__version__ = '1.0'
__author__ = 'xiawu@lubangame.com'

import logging
import os
import sys
import json
# network lib
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
from tornado import ioloop
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPResponse
from tornado import gen
import socket
import requests
import websocket_client
# django-related
from django.conf import settings
from config import codes
from provider import services as provider_services

logger = logging.getLogger(__name__)

#global variable
global loop_instance

# connect to full node by websocket
class FullNodeWebSocketClient(websocket_client.WebSocketClient):
    heartbeat_sched = None
    def __init__(self, url):
        super(FullNodeWebSocketClient, self).__init__()
        self.url = url
        self.send_counter = 0
        self.receive_counter = 0
        
    def _on_message(self, data):
        try:
            if not data:
                return
            message = json.loads(data)
            action = message['Action']
            if action == 'heartbeat': # ignore
                self.receive_counter += 1
                return
            if action == 'sendrawblock':
                self.__handle_block_message(message)
            elif action == 'sendblocktransactions':
                self.__handle_transaction_message(message)
        except Exception, inst:
            print "fail to handle message:", inst
            logger.exception("fail to handle message: %s" % str(inst))

    def __handle_block_message(self, message):
        global messageQueue
        
        blockhash = message['Result']['Hash']
        height = message['Result']['BlockData']['Height']
        data = message['Result']
        rest_url = settings.FULL_NODES['new']['rest_url']
        #provider_services.sync_block_rawdata(data)
        # enqueue
        messageQueue.put({'action': 'block', 'data': blockhash})

    def __handle_transaction_message(self, message):
        global messageQueue

        data = provider_services.parse_transaction_message(message['Result'])
        if data:
            messageQueue.put({'action': 'tx', 'data': data})
        
    def _on_connection_success(self):
        global loop_instance
        
        print "Start the heartbeat timer..."
        if self.heartbeat_sched: # cancel the previous timer
            self.heartbeat_sched.stop()
        self.heartbeat_sched = tornado.ioloop.PeriodicCallback(self.send_heartheat_message, 5 * 1000, io_loop=loop_instance)
        self.heartbeat_sched.start()
        
    def _on_connection_close(self):
        print "_on_connection_close"
    
    def _on_connection_error(self, exception):
        print "reconnect..."
        self.reconnect()

    def reconnect(self):
        self.connect(self.url)
        
    def send_heartheat_message(self):
        if self.receive_counter + 5 < self.send_counter:
            self.receive_counter = 0
            self.send_counter = 0
            self.reconnect()
            return
        self.send({"Action": "heartbeat", "Version": "1.0.0"})
        self.send_counter += 1
        # reset counter
        if self.send_counter > 10000:
            self.send_counter = 0
            self.receive_counter = 0
    
    def run(self):
        self.connect(self.url)

def query_full_node_task():
    ws_url = settings.FULL_NODES['new']['ws_url']
    fullNodeWebScoketClient = FullNodeWebSocketClient(ws_url)
    try:
        fullNodeWebScoketClient.run()
    except Exception, inst:
        print "query_full_node_task:", inst
        logger.exception("fail to execute full node task: %s" % str(inst))

def connect_full_node():
    global loop_instance
    try:
        loop_instance = ioloop.IOLoop.instance()
        loop_instance.add_callback(query_full_node_task)
        loop_instance.start()
    except Exception, inst:
        print "connect_full_node", inst
        logger.exception("fail to connect full node:%s" % str(inst));

def init_entry(queue):
    global messageQueue
    # fix the current queue
    messageQueue = queue
    print "connected to full node..."
    connect_full_node()

"""The command implemenation of monitor blockchain

"""

__copyright__ = """ Copyright (c) 2016 Beijing ShenJiangHuDong Technology Co., Ltd. All rights reserved."""
__version__ = '1.0'
__author__ = 'xiawu@lubangame.com'

import logging
import os
import sys
import json
import thread
# network lib
from flask import Flask, render_template
import socketio
import eventlet
import eventlet.wsgi
# django-related
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from config import codes
from provider import services as provider_services

logger = logging.getLogger(__name__)

# global variable
messageQueue = None
sendThread = None

# init the socket.io server
sio = socketio.Server(logger=False, async_mode='eventlet')
app = Flask(__name__)
app.wsgi_app = socketio.Middleware(sio, app.wsgi_app)
app.config['SECRET_KEY'] = 'secret!'

# The following is the event handler implementation of socket.io server

# send notify
def send_notify():
    global messageQueue
    while True:
        sio.sleep(10)
        while messageQueue.qsize() > 0:
            try:
                item = messageQueue.get()
                logger.info("send message:%s" % item['action'])
                sio.emit(item['action'], item['data'], namespace='/')
            except Exception, inst:
                logger.exception("fail to send message:%s" % str(inst))

@app.route('/')
def index():
    return "OK"

@sio.on('connect', namespace='/')
def on_connect(sid, environ):
    # init the send thread
    global sendThread
    if sendThread is None:
        sendThread = sio.start_background_task(send_notify)

@sio.on('disconnect', namespace='/')
def on_disconnect(sid):
    pass

def init_entry(queue):
    global messageQueue
    # fix the current queue
    messageQueue = queue
    print 'Listening on port %s' % settings.DEFAULT_MONITOR_PORT
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', settings.DEFAULT_MONITOR_PORT)), app, log_output=False)

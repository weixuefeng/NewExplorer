"""The command implemenation of monitor blockchain

"""

__copyright__ = """ Copyright (c) 2016 Beijing ShenJiangHuDong Technology Co., Ltd. All rights reserved."""
__version__ = '1.0'
__author__ = 'xiawu@lubangame.com'

import logging
import os
import sys
import json
import time
# proccess
from multiprocessing import Process, Manager
import signal
# django-related
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from config import codes
from provider import services as provider_services
# proccesses
import node
import server

logger = logging.getLogger(__name__)

# global variable
process_manager = None
message_queues = None
node_process_id = None
server_process_id = None

def close_process_handler(signum, frame):
    global node_process_id
    global server_process_id
    try:
        print "Quit"
        if node_process_id:
            print "kill node:", node_process_id
            os.kill(node_process_id, signal.SIGTERM)
        if server_process_id:
            print "kill server:", server_process_id
            os.kill(server_process_id, signal.SIGTERM)
        sys.exit(0)
    except Exception, inst:
        print inst
        logger.exception('fail to kill process: %s' % str(inst))

signal.signal(signal.SIGQUIT, close_process_handler)
signal.siginterrupt(signal.SIGQUIT, False)

class Command(BaseCommand):
    args = ''
    help = 'monitor blockchain'
    def handle(self, *args, **options):
        global process_manager
        global message_queues
        global node_process_id
        global server_process_id
        try:
            message_queues = {}
            process_manager = Manager()
            actionQueue = process_manager.Queue()
            message_queues['action'] = actionQueue
            # node
            node_process = Process(target=node.init_entry, args=(message_queues['action'],))
            node_process.start()
            node_process_id = node_process.pid
            print "node pid:", node_process_id
            # server
            server_process = Process(target=server.init_entry, args=(message_queues['action'],))
            server_process.start()
            server_process_id = server_process.pid
            print "server pid:", server_process_id
        except Exception, inst:
            print "fail to monitor blockchain:", inst
            logger.exception("fail to monitor blockchain:%s" % str(inst))
        finally:
            while True:
                time.sleep(3600)


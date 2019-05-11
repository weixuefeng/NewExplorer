"""Daemon for sync blockchain data form NewChain Node

"""

__copyright__ = """ Copyright (c) 2018 Newton Foundation. All rights reserved."""
__version__ = '1.0'
__author__ = 'xiawu@zeuux.org'

import logging
import os
import sys
import time
from multiprocessing import Process, Manager
import signal

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from config import codes
from . import blockchain_manager


logger = logging.getLogger(__name__)

class Command(BaseCommand):
    args = ''
    help = 'The deamon for sync blockchain'
    def handle(self, *args, **options):
        blockchain_type=codes.BlockChainType.NEWTON.value
        url_prefix = settings.FULL_NODES['new']['rest_url']
        manager = blockchain_manager.BlockchainSyncManager(blockchain_type, url_prefix)
        signal.signal(signal.SIGQUIT, manager.close_server_handler)
        signal.siginterrupt(signal.SIGQUIT, False)
        while True:
            manager.query_new_block()
            time.sleep(3)

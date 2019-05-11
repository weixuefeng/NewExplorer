"""Blockchain sync manager

"""

__copyright__ = """ Copyright (c) 2018 Newton Foundation. All rights reserved."""
__version__ = '1.0'
__author__ = 'xiawu@zeuux.org'

import logging
import time
import sys
import os
from multiprocessing import Process, Manager
import signal

from provider import services as provider_services
from . import indexing_server
from . import query_proxy
# from . import stats_server


logger = logging.getLogger(__name__)

class BlockchainSyncManager(object):
    def __init__(self, blockchain_type, url_prefix):
        self.blockchain_type = blockchain_type
        self.url_prefix = url_prefix
        self.manager = Manager()
        self.indexing_processes = []
        self.query_processes = []
        self.query_input_queues = []
        self.query_output_queue = None
        # self.stats_output_queue = None
        self.provider = provider_services.blockchain_providers[self.blockchain_type].Provider(self.url_prefix)
        self.current_height = self.provider.get_block_height() - 1 # always retrieve the previous block of current height
        self.__start_worker()
        
    def __start_worker(self):
        # Init the processes of indexing server
        self.query_output_queue = self.manager.Queue()
        # self.stats_output_queue = self.manager.Queue()
        for i in range(1):
            # init the input Queue
            query_input_queue = self.manager.Queue()
            self.query_input_queues.append(query_input_queue)
            # query proxy
            query_process = Process(target=query_proxy.init_entry, args=(self.blockchain_type, self.url_prefix, query_input_queue, self.query_output_queue))
            self.query_processes.append(query_process)
            query_process.start()
        # indexing server
        indexing_process = Process(target=indexing_server.init_entry, args=(self.blockchain_type, self.url_prefix, self.query_output_queue, ))
        self.indexing_processes.append(indexing_process)
        # stats_process = Process(target=stats_server.init_entry, args=(self.blockchain_type, self.url_prefix, self.stats_output_queue, ))
        # self.indexing_processes.append(stats_process)
        indexing_process.start()
        # stats_process.start()

    def query_new_block(self):
        try:
            height = self.provider.get_block_height()
            if height <= self.current_height:
                return
            # query
            qlen = len(self.query_input_queues)
            cnt = 0
            for tmp_height in range(self.current_height+1, height+1):
                idx = cnt % qlen
                self.query_input_queues[idx].put(tmp_height)
                cnt += 1
            # update the current height for preventing duplicate
            self.current_height = height
        except Exception, inst:
            logger.exception('fail to query new block:%s' % str(inst))

    def close_server_handler(self, signum, frame):
        try:
            logger.info("close_server_handler")
            for p in self.indexing_processes:
                try:
                    os.kill(p.pid, signal.SIGQUIT)
                except Exception, inst:
                    logger.exception("fail to kill proccess: pid %s" % p.pid)
            for p in self.query_processes:
                try:
                    os.kill(p.pid, signal.SIGQUIT)
                except Exception, inst:
                    logger.exception("fail to kill proccess: pid %s" % p.pid)
            sys.exit(0)
        except Exception, inst:
            logger.exception('fail to close server: %s' % str(inst))

    

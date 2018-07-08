"""Blockchain sync manager

"""

__copyright__ = """ Copyright (c) 2018 Newton Foundation. All rights reserved."""
__version__ = '1.0'
__author__ = 'xiawu@newtonproject.org'

import logging
import time
from multiprocessing import Process, Manager

from provider import services as provider_services
from . import indexing_server
from . import query_proxy

logger = logging.getLogger(__name__)

class BlockchainSyncManager(object):
    def __init__(self, blockchain_type, url_prefix):
        self.blockchain_type = blockchain_type
        self.url_prefix = url_prefix
        self.manager = Manager()
        self.indexing_processes = []
        self.query_processes = []
        self.query_input_queues = []
        self.query_output_queues = []
        self.current_height = provider_services.get_current_height(self.blockchain_type)
        self.provider = provider_services.blockchain_providers[self.blockchain_type].Provider(self.url_prefix)
        self.__start_worker()
        
    def __start_worker(self):
        # Init the processes of indexing server
        for i in range(20):
            # init the input Queue
            query_input_queue = self.manager.Queue()
            self.query_input_queues.append(query_input_queue)
            query_output_queue = self.manager.Queue()
            self.query_output_queues.append(query_output_queue)            
            # query proxy
            query_process = Process(target=query_proxy.init_entry, args=(self.blockchain_type, self.url_prefix, query_input_queue, query_output_queue, ))
            self.query_processes.append(query_process)
            query_process.start()
            # indexing server
            indexing_process = Process(target=indexing_server.init_entry, args=(self.blockchain_type, self.url_prefix, query_output_queue, ))
            self.indexing_processes.append(indexing_process)
            indexing_process.start()

    def query_new_block(self):
        try:
            height = self.provider.get_block_height()
            height = 100
            if height <= self.current_height:
                return
            # query
            qlen = len(self.query_input_queues)
            cnt = 0
            for tmp_height in range(self.current_height+1, height+1):
                idx = cnt % qlen
                self.query_input_queues[idx].put(tmp_height)
                cnt += 1
        except Exception, inst:
            logger.exception('fail to query new block:%s' % str(inst))
    

    

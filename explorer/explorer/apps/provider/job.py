# -*- coding: utf-8 -*-
"""Job for batch retrieve block information

"""

__copyright__ = """ Copyright (c) 2016 Newton Foundation. All rights reserved."""
__version__ = '1.0'
__author__ = 'xiawu@newtonproject.org'

import logging
import time
from threading import Thread

logger = logging.getLogger(__name__)


class FastSyncThread(Thread):
    """ Fast sync thread
    """
    def __init__(self, provider, storage_func, start_height, end_height):
        Thread.__init__(self)
        self.provider = provider
        self.start_height = start_height
        self.end_height = end_height
        self.storage_func = storage_func

    def run(self):
        try:
            current_height = self.start_height
            while current_height <= self.end_height:
                found_error = False
                data = None
                try:
                    data = self.provider.get_block_by_height(current_height)
                except:
                    pass
                if data:
                    self.storage_func(data, self.provider, is_fast_sync=True)
                    current_height += 1
        except Exception, inst:
            print inst
            logger.exception('fail to exeucte fast sync thread: %s' % str(inst))


class SyncAccountThread(Thread):
    """ Sync account thread
    """
    def __init__(self, provider, storage_func, address_list):
        Thread.__init__(self)
        self.provider = provider
        self.storage_func = storage_func
        self.address_list = address_list

    def run(self):
        try:
            logger.info("start the sync account thread")
            result = {}
            for address in self.address_list:
                value = self.provider.get_balance_by_address(address)
                result[address] = value
            self.storage_func(result)
        except Exception, inst:
            print inst
            logger.exception('fail to exeucte sync account thread: %s' % str(inst))


class SyncValidatorThread(Thread):
    def __init__(self, provider, storage_func, block_info, name ,url):
        Thread.__init__(self)
        self.provider = provider
        self.storage_func = storage_func
        self.name = name
        self.url = url
        self.block_info = block_info

    def run(self):
        try:
            logger.info("start the sync validator thread")
            self.storage_func(self.provider, self.block_info, self.name, self.url)
        except Exception, inst:
            print inst
            logger.exception('fail to exeucte sync validator thread: %s' % str(inst))

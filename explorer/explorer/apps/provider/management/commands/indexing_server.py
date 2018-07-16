"""Indexing Server

"""

__copyright__ = """ Copyright (c) 2018 Newton Foundation. All rights reserved."""
__version__ = '1.0'
__author__ = 'xiawu@newtonproject.org'

import logging
import time

from provider import services as provider_services

logger = logging.getLogger(__name__)
g_queue = None
g_provider = None


def run():
    global g_queue
    global g_provider
    try:
        while True:
            qsize = g_queue.qsize()
            for i in range(qsize):
                data = g_queue.get()
                if data:
                    provider_services.save_transaction_data(g_provider, data)
            time.sleep(0.1)
    except Exception, inst:
        logger.exception('fail to run:%s' % str(inst))


def init_entry(blockchain_type, url_prefix, input_queue):
    """Entry of indexing server
    
    :param int       blockchain_type: the type of blockchain
    :param str       url_prefix: the prefix of url
    :param Queue input_queue: the output data queue
    """
    global g_queue
    global g_provider
    g_queue = input_queue
    provider_services.init_transaction_cache()
    g_provider = provider_services.blockchain_providers[blockchain_type].Provider(url_prefix)
    run()
    

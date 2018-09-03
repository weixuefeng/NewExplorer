"""Proxy for retrieve information from NewChain Node

"""

__copyright__ = """ Copyright (c) 2018 Newton Foundation. All rights reserved."""
__version__ = '1.0'
__author__ = 'xiawu@newtonproject.org'

import logging
import time

from provider import services as provider_services

logger = logging.getLogger(__name__)
g_input_queue = []
g_output_queue = []
# g_stats_output_queue = []
g_provider = None

def run():
    global g_provider
    global g_input_queue
    global g_output_queue
    # global g_stats_output_queue
    try:
        while True:
            qsize = g_input_queue.qsize()
            for i in range(qsize):
                target_height = g_input_queue.get()
                logger.info("retrieve height:%s" % target_height)
<<<<<<< HEAD
                for j in range(5): # retry 5 times if network occured
=======
                for j in range(10): # retry 10 times if network occured
>>>>>>> ef02039f6a79f08c628c9c8bd3ea8b702847eb1b
                    data = g_provider.get_block_by_height(target_height)
                    if data:
                        g_output_queue.put(data)
                        # g_stats_output_queue.put(data)
                        break
            time.sleep(0.1)
    except:
        pass

def init_entry(blockchain_type, url_prefix, input_queue, output_queue):
    """Entry of indexing server

    :param int       blockchain_type: the type of blockchain
    :param str       url_prefix: the prefix of url
    :param Queue input_queue: the input data queue
    :param Queue output_queue: the output data queue
    """
    global g_input_queue
    global g_output_queue
    global g_provider
    # global g_stats_output_queue
    g_input_queue = input_queue
    g_output_queue = output_queue
    # g_stats_output_queue = stats_output_queue
    g_provider = provider_services.blockchain_providers[blockchain_type].Provider(url_prefix)
    run()

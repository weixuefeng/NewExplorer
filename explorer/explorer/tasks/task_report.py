# -*- coding: utf-8 -*-
__author__ = 'xiawu@xiawu.org'
__version__ = '$Rev$'
__doc__ = """  """

import logging
import os
import shutil
from celery import task
from django.conf import settings
from django.core.cache import cache
from config import codes
from provider import services as provider_services

logger = logging.getLogger(__name__)

@task()
def execute_sync_blockchain():
    try:
        blockchain_type=codes.BlockChainType.NEWTON.value
        url_prefix = settings.FULL_NODES['new']['rest_url']
        provider_services.sync_blockchain(url_prefix, blockchain_type)
        logger.info("execute_sync_blockchain:success")
    except Exception, inst:
        logger.error('fail to sync blockchain:%s' % str(inst))


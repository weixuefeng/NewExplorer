"""The command implemenation of sync blockchain

"""

__copyright__ = """ Copyright (c) 2016 Beijing ShenJiangHuDong Technology Co., Ltd. All rights reserved."""
__version__ = '1.0'
__author__ = 'xiawu@lubangame.com'

import logging
import os
import sys
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from config import codes
from provider import services as provider_services

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    args = ''
    help = 'sync blockchain'
    def handle(self, *args, **options):
        blockchain_type=codes.BlockChainType.NEWTON.value
        url_prefix = settings.FULL_NODES['ela']['rest_url']
        provider_services.sync_blockchain(url_prefix)

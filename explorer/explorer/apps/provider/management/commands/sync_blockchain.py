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
        if len(args) < 1:
            self.print_usage()
            return
        action = args[0]
        if action == 'fast_sync':
            blockchain_type=codes.BlockChainType.NEWTON.value
            url_prefix = settings.FULL_NODES['new']['rest_url']
            provider_services.fast_sync_blockchain(url_prefix)
        elif action == 'fill_missing':
            blockchain_type=codes.BlockChainType.NEWTON.value
            url_prefix = settings.FULL_NODES['new']['rest_url']
            provider_services.fill_missing_block(url_prefix)
        else:
            print "error action, choices:[fast_sync|fill_missing]"

    def print_usage(self):
        print "python manage.py sync_blockchain [fast_sync|fill_missing]"

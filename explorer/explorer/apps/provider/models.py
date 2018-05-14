"""The schema definition of blockchain

"""

__copyright__ = """ Copyright (c) 2016 Beijing ShenJiangHuDong Technology Co., Ltd. All rights reserved."""
__version__ = '1.0'
__author__ = 'xiawu@lubangame.com'

import logging
from django.conf import settings
from mongoengine import *
import datetime

logger = logging.getLogger(__name__)


class Block(Document):
    blockhash = StringField(max_length=128, required=True, primary_key=True)
    merkleroot = StringField(max_length=128, required=False)
    previousblockhash = StringField(max_length=128, required=True)
    tx = ListField(StringField(max_length=128))
    txlength = IntField()
    height = IntField()
    version = IntField(default=0)
    time = IntField()
    nonce = IntField()
    size = IntField()
    meta = { 'indexes': ['previousblockhash', 'height', 'time']}

class Transaction(Document):
    txid = StringField(max_length=128, required=True, primary_key=True)
    blockheight = IntField()
    blockhash = StringField(max_length=128, required=True)
    from_address = StringField(max_length=128, required=True)
    to_address = StringField(max_length=128, required=True)
    value = StringField(max_length=128, required=True)
    version = IntField(default=0)
    size = IntField(default=0)
    time = IntField()
    fees = IntField(default=0)
    fees_price = IntField(default=0)
    data = StringField(max_length=10240, required=False)
    transaction_index = IntField(default=0)
    locktime = IntField(default=0)
    meta = { 'indexes': ['blockhash', 'blockheight', 'time']}

class Address(Document):
    addr = StringField(max_length=128, required=True)
    txid = StringField(max_length=128, required=True)
    blockheight = IntField()
    time = IntField()
    value = StringField(max_length=128, required=True)
    vtype = IntField()
    n = IntField(default=0)
    locktime = IntField(default=0)
    meta = { 'indexes': ['addr', 'txid', 'blockheight', 'time', 'vtype']}

class Balance(Document):
    addr = StringField(max_length=128, required=True)
    value = FloatField(default=0)
    meta = { 'indexes': ['addr'] }

# init the connection
connect(settings.BLOCK_CHAIN_DB_NAME, host=settings.MONGODB_HOST)

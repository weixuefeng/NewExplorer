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
    blockhash = StringField(max_length=64, required=True, primary_key=True)
    merkleroot = StringField(max_length=64, required=True)
    previousblockhash = StringField(max_length=64, required=True)
    tx = ListField(StringField(max_length=64))
    txlength = IntField()
    height = IntField()
    version = IntField(default=0)
    time = IntField()
    confirmations = IntField()
    nonce = IntField()
    size = IntField()
    bits = IntField()
    difficulty = StringField()
    poolInfo = DictField()
    meta = { 'indexes': ['previousblockhash', 'height', 'time']}

class Transaction(Document):
    txid = StringField(max_length=64, required=True, primary_key=True)
    blockheight = IntField()
    blockhash = StringField(max_length=64, required=True)
    isCoinBase = BooleanField(default=False)
    valueOut = FloatField(default=0)
    version = IntField(default=0)
    vin = ListField(DictField())
    vout = ListField(DictField())
    size = IntField(default=0)
    time = IntField()
    fees = FloatField(default=0)
    confirmations = IntField(default=0)
    locktime = IntField(default=0)
    meta = { 'indexes': ['blockhash', 'blockheight', 'time']}

class Address(Document):
    addr = StringField(max_length=64, required=True)
    txid = StringField(max_length=64, required=True)
    blockheight = IntField()
    time = IntField()
    value = FloatField(default=0)
    vtype = IntField()
    n = IntField(default=0)
    locktime = IntField(default=0)
    meta = { 'indexes': ['addr', 'txid', 'blockheight', 'time', 'vtype']}

class Utxo(Document):
    addr = StringField(max_length=64, required=True)
    txid = StringField(max_length=64, required=True)
    blockheight = IntField()
    time = IntField()
    value = FloatField(default=0)
    vtype = IntField()
    n = IntField(default=0)
    locktime = IntField(default=0)
    meta = { 'indexes': ['addr', 'txid', 'blockheight', 'time', 'vtype']}

class Balance(Document):
    # temp_id = IntField()
    addr = StringField(max_length=64, required=True)
    value = FloatField(default=0)
    meta = { 'indexes': ['addr'] }

# init the connection
connect(settings.BLOCK_CHAIN_DB_NAME, host=settings.MONGODB_HOST)

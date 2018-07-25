"""The schema definition of blockchain

"""

__copyright__ = """ Copyright (c) 2016 Beijing ShenJiangHuDong Technology Co., Ltd. All rights reserved."""
__version__ = '1.0'
__author__ = 'xiawu@lubangame.com'

import logging
from django.conf import settings
from mongoengine import *


logger = logging.getLogger(__name__)


class Block(Document):
    blockhash = StringField(max_length=128, required=True, primary_key=True)
    merkleroot = StringField(max_length=128, required=False)
    previousblockhash = StringField(max_length=128, required=True)
    tx = ListField(StringField(max_length=128))
    txlength = IntField()
    height = LongField()
    version = IntField(default=0)
    time = LongField()
    nonce = StringField()
    size = LongField()
    meta = { 'indexes': ['previousblockhash', 'height', 'time']}

class Transaction(Document):
    txid = StringField(max_length=128, required=True, primary_key=True)
    blockheight = LongField()
    blockhash = StringField(max_length=128, required=True)
    from_address = StringField(max_length=128, required=True)
    to_address = StringField(max_length=128) # null if contract
    value = StringField(max_length=128, required=True)
    version = IntField(default=0)
    size = IntField(default=0)
    time = IntField()
    fees = LongField(default=0)
    fees_price = LongField(default=0)
    data = StringField(required=False)
    transaction_index = IntField(default=0)
    locktime = IntField(default=0)
    meta = { 'indexes': ['blockhash', 'blockheight', 'time', 'from_address', 'to_address']}


class CappedTransaction(Document):
    """Capped transaction collection for high performance memory access.
    Compared to transaction object, its column filed is short because it is only used for notification
    """
    txid = StringField(max_length=128, required=True, primary_key=True)
    blockheight = LongField()
    blockhash = StringField(max_length=128, required=True)
    from_address = StringField(max_length=128, required=True)
    to_address = StringField(max_length=128)
    value = StringField(max_length=128, required=True)
    time = IntField()
    meta = {'max_documents': 5000, 'max_size': 20000000}


class Account(Document):
    address = StringField(max_length=128, required=True, primary_key=True)
    balance = FloatField(default=0)
    total_received = FloatField(default=0)
    total_sent = FloatField(dafault=0)


# init the connection
connect(settings.BLOCK_CHAIN_DB_NAME, host=settings.MONGODB_HOST)

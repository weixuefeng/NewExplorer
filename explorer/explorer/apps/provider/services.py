"""The implementation of service layer for serveral blockchain information

"""

__copyright__ = """ Copyright (c) 2016 Beijing ShenJiangHuDong Technology Co., Ltd. All rights reserved."""
__version__ = '1.0'
__author__ = 'xiawu@lubangame.com'
import time
import logging
import threading
import math

from mongoengine import connect
from django.conf import settings
from django.core.cache import cache
from config import codes
import provider_newton
from provider import models as provider_models
from decimal import *
import job

DECIMAL_SATOSHI = Decimal("100000000")
logger = logging.getLogger(__name__)
blockchain_providers = {
    codes.BlockChainType.NEWTON.value: provider_newton
}

def get_current_height(blockchain_type=codes.BlockChainType.NEWTON.value):
    try:
        obj = provider_models.Block._get_collection().aggregate([
            { "$group": {
                "_id": None,
                "height": { "$max": "$height" }
            }}
        ])
        result = obj['result']
        if not result:
            return -1
        return result[0]['height']
    except Exception, inst:
        print inst
        return -1

def get_current_blockhash(blockchain_type=codes.BlockChainType.NEWTON.value):
    try:
        height = get_current_height(blockchain_type)
        if height < 0:
            return ''
        obj = provider_models.Block.objects.get(height=height)
        return obj.blockhash
    except Exception, inst:
        print inst
        return ""

def get_block_hash_by_height(height, blockchain_type=codes.BlockChainType.NEWTON.value):
    try:
        obj = provider_models.Block.objects.get(height=height)
        return obj.blockhash
    except Exception, inst:
        print inst
        return ''

def store_block_data(block_info, provider, blockchain_type=codes.BlockChainType.NEWTON.value, is_fast_sync=True):
    """Store the block info
    """
    try:
        if not is_fast_sync:
            current_blockhash = get_current_blockhash(blockchain_type)
            previous_blockhash = block_info['previousblockhash']
            if  len(current_blockhash) > 0 and current_blockhash != previous_blockhash: # find a block fork
                logger.error("find a block fork at: height %s, current_blockhash %s, previous_blockhash %s" % (block_info['height'], current_blockhash, previous_blockhash))
                return False
        block_instance = provider_models.Block()
        for k, v in block_info.items():
            setattr(block_instance, k, v)
        txlength = block_instance.txlength
        if txlength > 0:
            # get transactions
            for item in block_info['transactions']:
                tx_item = provider.parse_transaction_response(item)
                transaction_info = tx_item
                txid = transaction_info['txid']
                transaction_instance = provider_models.Transaction()
                for k, v in transaction_info.items():
                    setattr(transaction_instance, k, v)
                transaction_instance.blockhash = block_info['blockhash']
                transaction_instance.blockheight = block_info['height']
                transaction_instance.time = block_info['time']
                transaction_instance.save()
        # when transaction is finish, store block
        block_instance.save()
        return True
    except Exception, inst:
        print inst
        logger.exception("fail to store block data:%s, block_info:%s" % (str(inst), block_info))
        return False

def save_block_data(block_info):
    """Save the block info
    """
    try:
        block_instance = provider_models.Block()
        for k, v in block_info.items():
            setattr(block_instance, k, v)
        block_instance.save()
        return True
    except Exception, inst:
        print inst
        logger.exception("fail to save block data:%s, block_info:%s" % (str(inst), block_info))
        return False


def init_transaction_cache():
    """Initialize the transaction cache

    :return: the execution status, True is success, False is fail
    :rtype: bool
    """
    try:
        provider_models.CappedTransaction.drop_collection()
        return True
    except Exception, inst:
        logger.exception("fail to initialize transaction cache:%s" % str(inst))
        return False


def insert_transactions_to_cache(transactions):
    """Insert the transactions to cache (capped collection)

    :param object transaction:  The transaction object
    :return: the execution status, True is success, False is fail
    :rtype: bool
    """
    try:
        items = []
        for item in transactions:
            capped_instance = provider_models.CappedTransaction()
            for k in item:
                setattr(capped_instance, k, getattr(item, k))
            capped_instance._created = True
            items.append(capped_instance)
        provider_models.CappedTransaction.objects.insert(items)
        return True
    except Exception, inst:
        logger.exception("fail to insert transaction to cache:%s" % str(inst))
        return False


def sync_account_data(provider, address_list):
    """Sync the data of account
    """
    try:
        def store_account_data(result):
            for address,balance in result.items():
                instance = provider_models.Account.objects.filter(address=address).first()
                if not instance:
                    instance = provider_models.Account()
                    instance.address = address
                instance.balance = balance
                instance.save()
        # start sync thread
        thread_instance = job.SyncAccountThread(provider, store_account_data, address_list)
        thread_instance.start()
    except Exception, inst:
        logger.exception("fail to sync account data:%s" % str(inst))


def save_transaction_data(provider, block_info):
    """Save the transaction info
    """
    try:
        transactions = []
        address_list = []
        for item in block_info['transactions']:
            tx_item = provider.parse_transaction_response(item)
            transaction_info = tx_item
            txid = transaction_info['txid']
            transaction_instance = provider_models.Transaction()
            for k, v in transaction_info.items():
                setattr(transaction_instance, k, v)
            transaction_instance.blockhash = block_info['blockhash']
            transaction_instance.blockheight = block_info['height']
            transaction_instance.time = block_info['time']
            transaction_instance._created = True
            transactions.append(transaction_instance)
            address_list.append(transaction_instance.from_address)
            address_list.append(transaction_instance.to_address)
        if transactions:
            provider_models.Transaction.objects.insert(transactions)
            # cache transaction
            insert_transactions_to_cache(transactions)
            sync_account_data(provider, list(set(address_list)))
        return True
    except Exception, inst:
        print inst
        logger.exception("fail to save transaction data:%s" % (str(inst)))
        return False

        
def delete_data_by_block_height(height):
    provider_models.Block.objects.filter(height__gte=height).delete()
    provider_models.Transaction.objects.filter(blockheight__gte=height).delete()

def handle_block_fork(blockchain_type):
    """Handle the block fork
        if it occurs, delete all block data
    """
    try:
        logger.info("start to handle block fork...")
        url_prefix = settings.FULL_NODES['new']['rest_url']
        current_height = get_current_height(blockchain_type=blockchain_type)
        target_height = current_height - 20
        delete_data_by_block_height(target_height)
        sync_blockchain(url_prefix, blockchain_type=blockchain_type, from_height=target_height)
        logger.info("handle block fork successfully.")
        return True
    except Exception, inst:
        print "fail to handle block fork:", str(inst)
        logger.exception("fail to handle block fork: %s" % str(inst))
        return False


def sync_block_rawdata(data, blockchain_type=codes.BlockChainType.NEWTON.value):
    """Sync the block raw info
    """
    try:
        provider = blockchain_providers[blockchain_type].Provider('')
        block_info = provider.parse_block_info(data)
        status = store_block_data(block_info)
        if not status:
            handle_block_fork(blockchain_type)
    except Exception, inst:
        print inst
        logger.exception("fail to sync block raw data:%s" % str(inst))


def sync_blockchain(url_prefix, blockchain_type=codes.BlockChainType.NEWTON.value, from_height=None):
    """Sync the blockchain info from full node to database
    """
    try:
        provider = blockchain_providers[blockchain_type].Provider(url_prefix)
        if not from_height:
            # query the current height
            current_height = get_current_height(blockchain_type)
        else:
            current_height = from_height
        logger.info("sync_blockchain:current_height:%s" % current_height)
        # query the height of blockchain
        height = provider.get_block_height()
        if height <= current_height:
            logger.info("sync_blockchain:no new block")
            return
        status = True
        for tmp_height in range(current_height+1, height+1):
            # get block info
            data = provider.get_block_by_height(tmp_height)
            status = store_block_data(data, provider)
            if not status:
                break
            logger.info("sync_blockchain:height:%s" % tmp_height)
        if not status:
            handle_block_fork(blockchain_type)
    except Exception, inst:
        print "fail to sync blockchain", inst
        logger.exception("fail to sync blockchain:%s" % str(inst))


def fast_sync_blockchain(url_prefix, blockchain_type=codes.BlockChainType.NEWTON.value, from_height=None):
    """Fast sync the blockchain info from full node to database
    """
    try:
        provider = blockchain_providers[blockchain_type].Provider(url_prefix)
        if not from_height:
            # query the current height
            current_height = get_current_height(blockchain_type)
        else:
            current_height = from_height
        logger.info("sync_blockchain:current_height:%s" % current_height)
        # query the height of blockchain
        height = provider.get_block_height()
        if height <= current_height:
            logger.info("sync_blockchain:no new block")
            return
        MAX_THREADS = 50
        all_threads = []
        height_diff = height - current_height
        step = int(math.ceil(height_diff / MAX_THREADS))
        if step < 1:
            step = 1
        number_of_use = int(height_diff / step)
        start_height = current_height + 1
        for i in range(number_of_use):
            end_height = start_height + step
            if end_height > height:
                end_height = height
            thread_instance = job.FastSyncThread(provider, store_block_data, start_height, end_height)
            thread_instance.start()
            all_threads.append(thread_instance)
            start_height = end_height + 1
        while True:
            is_all_close = True
            for item in all_threads:
                if item.isAlive():
                    is_all_close = False
            if is_all_close:
                break
        print "sync successfully."
    except Exception, inst:
        print "fail to fast sync blockchain", inst
        logger.exception("fail to fast sync blockchain:%s" % str(inst))


def fill_missing_block(url_prefix, blockchain_type=codes.BlockChainType.NEWTON.value):
    """Retrieve the missing blocks according to current block database
    """
    try:
        provider = blockchain_providers[blockchain_type].Provider(url_prefix)
        # query the current height
        current_height = get_current_height(blockchain_type)
        for tmp_height in range(current_height):
            data = get_block_hash_by_height(tmp_height)
            if not data:
                try:
                    data = provider.get_block_by_height(tmp_height)
                except:
                    pass
                if data:
                    store_block_data(data, provider, is_fast_sync=True)
                    print "retrieve missing block:", tmp_height
    except Exception, inst:
        print "fail to fill missing block", inst
        logger.exception("fail to fill missing block:%s" % str(inst))

    
def send_transaction(rawtx, blockchain_type=codes.BlockChainType.NEWTON.value):
    """Send transaction
    
    """
    try:
        url_prefix = settings.FULL_NODES['new']['rest_url']
        provider = blockchain_providers[blockchain_type].Provider(url_prefix)
        return provider.send_transaction(rawtx)
    except Exception, inst:
        print inst
        logger.exception("fail to send transaction:%s" % str(inst))
        return None

def get_transaction_pool(blockchain_type=codes.BlockChainType.NEWTON.value):
    """Get the transaction list in memory pool
    
    """
    try:
        url_prefix = settings.FULL_NODES['new']['rest_url']
        provider = blockchain_providers[blockchain_type].Provider(url_prefix)
        return provider.get_transaction_pool()
    except Exception, inst:
        print inst
        logger.exception("fail to get transaction list in memory pool:%s" % str(inst))
        return []

def parse_transaction_message(data, blockchain_type=codes.BlockChainType.NEWTON.value):
    """Parse the transaction message
    
    """
    try:
        provider = blockchain_providers[blockchain_type].Provider('')
        return provider.parse_transaction_response(data)
    except Exception, inst:
        print inst
        logger.exception("fail to parse transaction message:%s" % str(inst))
        return None


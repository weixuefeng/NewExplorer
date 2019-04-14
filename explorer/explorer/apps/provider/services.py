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
import binascii
from mongoengine.queryset.visitor import Q


DECIMAL_SATOSHI = Decimal("100000000")
CONFIRM_BLOCKS = 6
logger = logging.getLogger(__name__)
blockchain_providers = {
    codes.BlockChainType.NEWTON.value: provider_newton
}

def get_current_height(blockchain_type=codes.BlockChainType.NEWTON.value):
    try:
        stats = provider_models.Statistics.objects.filter(sync_type=codes.SyncType.SYNC_PROGRAM.value).first()
        if stats and stats.block_height:
            return stats.block_height
        rs = provider_models.Block._get_collection().aggregate([{ "$group": {
            "_id": None,
            "height": { "$max": "$height" }
            }}
        ])
        if not rs.alive:
            return -1
        obj = rs.next()
        if not obj:
            return -1
        return obj['height']
    except Exception, inst:
        print "inst:", inst
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

def store_block_data(provider, block_info, blockchain_type=codes.BlockChainType.NEWTON.value, is_fast_sync=True):
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
        block_instance['validator'] = ''
        block_instance.save()
        return True
    except Exception, inst:
        print inst
        logger.exception("fail to store block data:%s, block_info:%s" % (str(inst), block_info))
        return False


def sync_validator_data(provider, block_info, name="", url=""):
    """sync the data of validator
    """
    try:
        instance = provider_models.Validator.objects.filter(address=block_info['validator']).first()
        if not instance:
            instance = provider_models.Validator()
            instance.address = block_info['validator']
            instance.name = name
            instance.url = url
            instance.save()
    except Exception, inst:
        logger.exception("fail to sync validator data:%s" % str(inst))


def save_block_data(provider, block_info, sync_type=codes.SyncType.SYNC_PROGRAM.value, contracts_number=0):
    """Save the block info
    """
    try:
        block_instance = provider_models.Block()
        for k, v in block_info.items():
            setattr(block_instance, k, v)
        if block_info['height'] == 0:
            pass
        else:
            sync_validator_data(provider, block_info)
        block_instance.save()

        # update stats
        block_height = block_info['height']
        transactions_number = block_info['txlength']
        stats = provider_models.Statistics.objects.filter(sync_type=sync_type).first()
        if not stats:
            stats = provider_models.Statistics()
            stats.sync_type = sync_type
        if sync_type == codes.SyncType.SYNC_PROGRAM.value:
            if not stats.block_height and stats.block_height > block_height:
                logger.error('block height exception:stats.block_height > block_height')
            else:
                stats.block_height = block_height
        elif sync_type in [codes.SyncType.FILL_MISSING_PROGRAM.value, codes.SyncType.REINDEX_PROGRAM.value]:
            pass
        else:
            logger.error("unsupported sync type")
            return False
        if sync_type in [codes.SyncType.SYNC_PROGRAM.value, codes.SyncType.FILL_MISSING_PROGRAM.value]:
            stats.transactions_number += transactions_number
            stats.contracts_number += contracts_number
            stats.save()
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
    items = []
    try:
        for item in transactions:
            capped_instance = provider_models.CappedTransaction()
            for k in item:
                setattr(capped_instance, k, getattr(item, k))
            capped_instance._created = True
            items.append(capped_instance)
        provider_models.CappedTransaction.objects.insert(items)
        return True
    except Exception, inst:
        # reset the capped collection
        try:
            init_transaction_cache()
            insert_transactions_to_cache(transactions)
        except:
            pass
        logger.exception("fail to insert transaction to cache:%s" % str(inst))
        return False


def sync_account_data(provider, address_list, address_dict, sync_type=codes.SyncType.SYNC_PROGRAM.value):
    """Sync the data of account
    """
    try:
        result = {}
        for address in address_list:
            value = provider.get_balance_by_address(address)
            result[address] = value
        for address,balance in result.items():
            instance = provider_models.Account.objects.filter(address=address).first()
            if not instance:
                instance = provider_models.Account()
                instance.address = address
            instance.balance = balance
            if sync_type == codes.SyncType.SYNC_PROGRAM.value:
                instance.transactions_number += address_dict[address]
            elif sync_type == codes.SyncType.FILL_MISSING_PROGRAM.value:
                instance.missing_transactions_number += address_dict[address]
            instance.save()
    except Exception, inst:
        logger.exception("fail to sync account data:%s" % str(inst))


def save_transaction_data(provider, block_info, sync_type=codes.SyncType.SYNC_PROGRAM.value, is_cached=True):
    """Save the transaction info
    """
    try:
        transactions = []
        address_list = []
        contracts_number = 0

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
            if not transaction_instance.to_address:
                contracts_number += 1
                receipt = provider.get_transaction_receipt(txid)
                transaction_instance.to_address = receipt['contract_address']
                sync_contract_data(receipt, block_info['time'])
                address_list.append(transaction_instance.to_address)
            else:
                address_list.append(transaction_info['to_address'])
            transactions.append(transaction_instance)
            if not transaction_info['to_address'] == transaction_info['from_address']:
                address_list.append(transaction_info['from_address'])
        # save transactions
        if transactions:
            provider_models.Transaction.objects.insert(transactions)
            # cache transaction
            if is_cached:
                insert_transactions_to_cache(transactions)
            address_dict = {}
            for address in set(address_list):
                address_dict[address] = address_list.count(address)
            sync_account_data(provider, list(set(address_list)), address_dict, sync_type)
        return True, contracts_number
    except Exception, inst:
        print inst
        logger.exception("fail to save transaction data:%s" % (str(inst)))
        return False, 0

def sync_contract_data(receipt_data, time):
    """Save the contract info
    """
    try:
        contract_instance = provider_models.Contract()
        contract_instance.contract_address = receipt_data['contract_address']
        contract_instance.create_tx = receipt_data['txid']
        contract_instance.creator = receipt_data['from_address']
        contract_instance.time = time
        contract_instance.save()
    except Exception, inst:
        print inst
        logger.exception('fail to sync contract data:%s' % (str(inst)))
        return False

def sync_address_data(transaction_instance):
    """Save the address info
    """
    try:
        to_address = transaction_instance.to_address
        from_address = transaction_instance.from_address
        if to_address == from_address:
            addr_obj = provider_models.Address()
            addr_obj.address = to_address
            addr_obj.txid = transaction_instance.txid
            addr_obj.time = transaction_instance.time
            addr_obj.save()
        else:
            to_addr_obj = provider_models.Address()
            to_addr_obj.address = to_address
            to_addr_obj.txid = transaction_instance.txid
            to_addr_obj.time = transaction_instance.time
            to_addr_obj.save()
            from_addr_obj = provider_models.Address()
            from_addr_obj.address = from_address
            from_addr_obj.txid = transaction_instance.txid
            from_addr_obj.time = transaction_instance.time
            from_addr_obj.save()
    except Exception, inst:
        print inst
        logger.exception('fail to save address data:%s' % (str(inst)))
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
        sync_type = codes.SyncType.SYNC_PROGRAM.value
        provider = blockchain_providers[blockchain_type].Provider(url_prefix)
        if not from_height:
            # query the current height
            current_height = get_current_height(blockchain_type)
        else:
            current_height = from_height
        logger.info("sync_blockchain:current_height:%s" % current_height)
        # query the height of blockchain
        height = provider.get_block_height()
        if height > CONFIRM_BLOCKS: # waiting for some blocks confirmation
            height -= CONFIRM_BLOCKS
        if height <= current_height:
            logger.info("sync_blockchain:no new block")
            return
        for tmp_height in range(current_height+1, height+1):
            # get block info
            data = provider.get_block_by_height(tmp_height)
            if data:
                status = save_transaction_data(provider, data, sync_type=sync_type)
                if status[0]:
                    contracts_number = status[1]
                    save_block_data(provider, data, sync_type=sync_type, contracts_number=contracts_number)
            logger.info("sync_blockchain:height:%s" % tmp_height)
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


def fill_missing_block(url_prefix, blockchain_type=codes.BlockChainType.NEWTON.value, start_height=0, end_height=0):
    """Retrieve the missing blocks according to current block database
    """
    try:
        sync_type = codes.SyncType.FILL_MISSING_PROGRAM.value
        provider = blockchain_providers[blockchain_type].Provider(url_prefix)
        # query the current height
        current_height = get_current_height(blockchain_type)
        if current_height == -1:
            start_height = 0
        if start_height > current_height or end_height > current_height:
            print "error: start_height > current_height"
            return
        if end_height == 0:
            end_height = current_height
        for tmp_height in range(start_height, end_height + 1):
            data = get_block_hash_by_height(tmp_height)
            if not data:
                try:
                    data = provider.get_block_by_height(tmp_height)
                except:
                    pass
                if data:
                    # delete wrong data
                    provider_models.Transaction.objects.filter(blockheight=tmp_height).delete()
                    status = save_transaction_data(provider, data, sync_type=sync_type, is_cached=False)
                    if status[0]:
                        contracts_number = status[1]
                        save_block_data(provider, data, sync_type=sync_type, contracts_number=contracts_number)
                        logger.info("sync missing block:%s" % tmp_height)
    except Exception, inst:
        print "fail to fill missing block", inst
        logger.exception("fail to fill missing block:%s" % str(inst))


def reindex_block(url_prefix, blockchain_type=codes.BlockChainType.NEWTON.value, start_height=0, end_height=0):
    """Re-Indexing blocks according to current block database
    """
    try:
        sync_type = codes.SyncType.REINDEX_PROGRAM.value
        provider = blockchain_providers[blockchain_type].Provider(url_prefix)
        # query the current height
        current_height = get_current_height(blockchain_type)
        if current_height == -1:
            start_height = 0
        if start_height > current_height or end_height > current_height:
            print "error: start_height > current_height"
            return
        if end_height == 0:
            end_height = current_height
        for tmp_height in range(start_height, end_height + 1):
            data = provider.get_block_by_height(tmp_height)
            if data:
                # delete wrong data
                provider_models.Block.objects.filter(height=tmp_height).delete()
                provider_models.Transaction.objects.filter(txid__in=[item['hash'] for item in data['transactions']]).delete()
                provider_models.Transaction.objects.filter(blockheight=tmp_height).delete()
                status = save_transaction_data(provider, data, sync_type=sync_type, is_cached=False)
                if status[0]:
                    contracts_number = status[1]
                    save_block_data(provider, data, sync_type=sync_type, contracts_number=contracts_number)
                    logger.info("reindex block:%s" % tmp_height)
    except Exception, inst:
        logger.exception("fail to reindexing block:%s" % str(inst))


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

def totalize_account_transactions():
    """First stop syncing data, then calculate the total number of transactions for all accounts.

    """
    try:
        account_objs = provider_models.Account.objects.filter()
        for account in account_objs:
            print "caculate address:", account.address
            if account.transactions_number:
                continue
            tx_number = provider_models.Address.objects.filter(address=account.address).count()
            account.transactions_number = tx_number
            account.save()
        stats = provider_models.Statistics.objects.filter(sync_type=codes.SyncType.SYNC_PROGRAM.value).first()
        if not stats:
            stats = provider_models.Statistics()
            stats.sync_type = codes.SyncType.SYNC_PROGRAM.value
        txs_number = provider_models.Transaction.objects.filter().count()
        contracts_number = provider_models.Contract.objects.filter().count()
        stats.transactions_number = txs_number
        stats.contracts_number = contracts_number
        stats.save()
    except Exception, inst:
        print inst
        logger.exception("fail to totalize account transactions:%s" % str(inst))
        return None

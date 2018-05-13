"""The implementation of service layer for serveral blockchain information

"""

__copyright__ = """ Copyright (c) 2016 Beijing ShenJiangHuDong Technology Co., Ltd. All rights reserved."""
__version__ = '1.0'
__author__ = 'xiawu@lubangame.com'
import time
import logging
from mongoengine import connect
from django.conf import settings
from django.core.cache import cache
from config import codes
import provider_newton
from provider import models as provider_models
from decimal import *

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

def store_block_data(block_info, blockchain_type=codes.BlockChainType.NEWTON.value, is_fast_sync=False):
    """Store the block info
    """
    try:
        current_blockhash = get_current_blockhash(blockchain_type)
        previous_blockhash = block_info['previousblockhash']
        if len(current_blockhash) > 0 and current_blockhash != previous_blockhash: # find a block fork
            logger.error("find a block fork at: height %s, current_blockhash %s, previous_blockhash %s" % (block_info['height'], current_blockhash, previous_blockhash))
            return False
        if len(current_blockhash) == 0 and not is_fast_sync: # the db is empty
            logger.info("db is empty...")
            return False
        block_instance = provider_models.Block()
        for k, v in block_info.items():
            setattr(block_instance, k, v)
        # get transactions
        for tx_item in block_info['tx_detail']:
            transaction_info = tx_item
            txid = transaction_info['txid']
            transaction_instance = provider_models.Transaction()
            for k, v in transaction_info.items():
                setattr(transaction_instance, k, v)
            transaction_instance.blockhash = block_info['blockhash']
            transaction_instance.blockheight = block_info['height']
            transaction_instance.save()
            # record the last block and transaction
            newblock_hash = block_info['blockhash']
            newtx_hash = txid
            # indexing address
            # for receive
            vin = transaction_info.get('vin', [])
            if vin:
                for item in vin:
                    addr = item.get('addr')
                    value = item.get('value')
                    previous_txid = item.get('txid')
                    n = item['n']
                    if addr and value:
                        obj = provider_models.Address()
                        obj.addr = addr
                        obj.txid = txid
                        obj.blockheight = block_info['height']
                        obj.value = float(value)
                        obj.vtype = codes.ValueType.SEND.value
                        obj.n = n
                        obj.time = transaction_instance.time
                        obj.save()
                        obju = provider_models.Utxo()
                        obju.addr = addr
                        obju.txid = previous_txid
                        obju.blockheight = block_info['height']
                        obju.value = float(value)
                        obju.vtype = codes.ValueType.SEND.value
                        obju.n = n
                        obju.time = transaction_instance.time
                        obju.save()
                        # sum balance
                        balance = provider_models.Balance.objects.filter(addr=addr).first()
                        if balance:
                            value = float(balance.value) - float(value)
                            balance.value = value
                            balance.save()
                        else:
                            balance = provider_models.Balance()
                            balance.addr = addr
                            balance.value = float(value)
                            balance.save()
            # for send
            vout = transaction_info.get('vout', [])
            if vout:
                for item in vout:
                    addr = item['scriptPubKey']['addresses'][0]
                    value = item['value']
                    n = item['n']
                    if addr:
                        obj = provider_models.Address()
                        obj.addr = addr
                        obj.txid = txid
                        obj.blockheight = block_info['height']
                        obj.value = value
                        obj.vtype = codes.ValueType.RECEIVE.value
                        obj.n = n
                        obj.locktime = transaction_instance.locktime
                        obj.time = transaction_instance.time
                        obj.save()
                        obju = provider_models.Utxo()
                        obju.addr = addr
                        obju.txid = txid
                        obju.blockheight = block_info['height']
                        obju.value = value
                        obju.vtype = codes.ValueType.RECEIVE.value
                        obju.n = n
                        obju.locktime = transaction_instance.locktime
                        obju.time = transaction_instance.time
                        obju.save()
                        # sum balance
                        balance = provider_models.Balance.objects.filter(addr=addr).first()
                        if balance:
                            value = float(balance.value) + float(value)
                            balance.value = value
                            balance.save()
                        else:
                            balance = provider_models.Balance()
                            balance.addr = addr
                            balance.value = float(value)
                            balance.save()

        # when transaction is finish, store block
        block_instance.save()
        return True
    except Exception, inst:
        print "fail to store block data:", inst
        logger.exception("fail to store block data:%s" % str(inst))
        return False

def delete_data_by_block_height(height):
    provider_models.Block.objects.filter(height__gt=height).delete()
    provider_models.Transaction.objects.filter(blockheight__gt=height).delete()
    provider_models.Address.objects.filter(blockheight__gt=height).delete()

def handle_block_fork(blockchain_type):
    try:
        logger.info("start to handle block fork...")
        url_prefix = settings.FULL_NODES['ela']['rest_url']
        current_height = get_current_height(blockchain_type)
        target_height = current_height - 20
        if target_height < 0:
            target_height = 0
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
        newblock_hash = ''
        newtx_hash = ''
        status = True
        for tmp_height in range(current_height+1, height+1):
            # get block info
            data = provider.get_block_by_height(tmp_height)
            status = store_block_data(data, is_fast_sync=True)
            if not status:
                break
            logger.info("sync_blockchain:height:%s" % tmp_height)
        if not status:
            handle_block_fork(blockchain_type)
    except Exception, inst:
        print "fail to sync blockchain", inst
        logger.exception("fail to sync blockchain:%s" % str(inst))

def __get_utxo_from_localdb(address, blockchain_type):
    result = []
    height = get_current_height()
    if isinstance(address,list):
        r = provider_models.Utxo._get_collection().find({"addr" : {"$in" : address}})
    else:
        r = provider_models.Utxo._get_collection().find({"addr" : address})
    if r :
        receive_container = []
        send_container = []
        for item in r:
            item['ts'] = item['time']
            item['count'] = 1
            item['amount'] = item['value']
            item['address'] = item['addr']
            item['vout'] = item['n']
            if item['vtype'] == codes.ValueType.RECEIVE.value:
                receive_container.append(item)
            if item['vtype'] == codes.ValueType.SEND.value:
                send_container.append(item)

        result_container = []
        for receive_item in receive_container:
            found = True
            for send_item in send_container:
                if send_item['txid'] == receive_item['txid'] and send_item['value'] == receive_item['value'] and send_item['n'] == receive_item['n']:
                    found = False
                    break                
            if found:
                result_container.append(receive_item)
                
        for item in result_container:
                new_item = {}
                new_item['address'] = item['address']
                new_item['vout'] = item['vout']
                new_item['amount'] = item['amount']
                new_item['satoshis'] = int(Decimal(str(item['amount'])) * DECIMAL_SATOSHI)
                new_item['confirmations'] = height - item['blockheight']
                new_item['ts'] = item['ts']
                new_item['locktime'] = item['locktime']
                new_item['height'] = height
                new_item['txid'] = item['txid']
                new_item['scriptPubKey'] = ''
                result.append(new_item)
    return result
    
def get_utxo_by_address(address, blockchain_type=codes.BlockChainType.NEWTON.value):
    """Get the utxo list by given address
    
    """
    try:
        return __get_utxo_from_localdb(address, blockchain_type)
        #url_prefix = settings.FULL_NODES['ela']['rest_url']
        #provider = blockchain_providers[blockchain_type].Provider(url_prefix)
        #return provider.get_utxo_by_address(address)
    except Exception, inst:
        print inst
        logger.exception("fail to get utxo by address:%s" % str(inst))
        return []

def send_transaction(rawtx, blockchain_type=codes.BlockChainType.NEWTON.value):
    """Send transaction
    
    """
    try:
        url_prefix = settings.FULL_NODES['ela']['rest_url']
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
        url_prefix = settings.FULL_NODES['ela']['rest_url']
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


# -*- coding: utf-8 -*-
__author__ = 'xiawu@zeuux.org'
__version__ = '$Rev$'
__doc__ = """  """

import logging
import datetime
import time
import json
import sys
from decimal import *
from django.conf import settings
from django.core.cache import cache
from django.utils.translation import ugettext as _
from config import codes
from utils import http
from provider import models as provider_models
from provider import services as provider_services
DECIMAL_SATOSHI = Decimal("1000000000000000000")
from utils import newchain_tools
import datetime
from pymongo import MongoClient
from mongoengine.queryset.visitor import Q

addr_translation = newchain_tools.NewChainAddress()
logger = logging.getLogger(__name__)

# internal utils functions

def __convert_transaction_to_json(obj):
    result = json.loads(obj.to_json())
    result['txid'] = obj.id
    result['blocktime'] = obj.time
    result['fees'] = obj.fees
    result['fees_price'] = obj.fees_price
    # vouts = obj['vout']
    # for v in vouts:
    #     v['value'] = __convert_num_to_float(v['value'])
    # result['vout'] = vouts
    result['valueOut'] = __convert_num_to_float(obj['value'])
    return result

def __convert_transaction_to_client_json(obj):
    result = json.loads(obj.to_json())
    result['id'] = obj.id
    result['operations'] = []
    result['contract']= ''
    result['blockNumber'] = int(obj.blockheight)
    result['timeStamp'] = str(obj.time)
    result['nonce'] = 0 
    result['from'] = obj.from_address
    result['to'] = obj.to_address 
    result['value'] = str(obj.value)
    result['input'] = obj.data
    result['gas'] = str(obj.fees)
    result['gasPrice'] = str(obj.fees_price)
    result['_id'] = obj.id
    result['error'] = ""
    result['gasUsed'] = str(obj.fees)
    return result

def __convert_num_to_float(num):
    res = float(Decimal(str(num)) / DECIMAL_SATOSHI)
    return res

def __convert_account_to_json(obj):
    result = json.loads(obj.to_json())
    return result

def __convert_contract_to_json(obj):
    result = json.loads(obj.to_json())
    result['contract_address'] = obj.id
    result['time'] = obj.time
    result['creator'] = obj.creator
    result['create_tx'] = obj.create_tx
    return result

def handle_validator(address):
    obj = provider_models.Validator.objects.filter(address=address).first()
    validator = json.loads(obj.to_json())
    url = validator['url']
    name = validator['name']
    return name, url

# API functions
def api_ping(request, version):
    return http.JsonSuccessResponse()

def api_get_ip(request, version):
    ip = misc.get_client_ip(request)
    return http.JsonSuccessResponse({'ip': ip})

def api_get_peer(request,version):
    return http.JsonResponse({"connected":true,"host":"127.0.0.1","port":""})

def api_show_version(request, version):
    """Show the api version for uri: /version
    """
    return http.JsonResponse({'version': '1.0'})

def api_get_sync(request, version):
    """ show the sync status summary for uri: /sync 
    """
    try:
        current_height = provider_services.get_current_height()
        today = datetime.datetime.now() + datetime.timedelta(minutes=-2)
        start_ts = (today - datetime.datetime(1970, 1, 1)).total_seconds()
        result = {
            "blockChainHeight": current_height,
            "height": current_height,
            "status": _("finished"),
            "syncPercentage": 100,
            "type": _("newton supernode"),
            "startTs": int(start_ts) * 1000,
            "syncedBlocks": current_height,
            }
        return http.JsonResponse(result)
    except Exception, inst:
        print inst
        logger.exception("fail to get sync:%s" % str(inst))
        return http.HttpResponseServerError()

def api_get_status(request, version):
    """ show the status info for uri: /status
    """
    current_height = provider_services.get_current_height()
    current_net = settings.CURRENT_NET
    result = {
        "info": {
            "blocks": current_height,
            "connections": 1,
            "difficulty": 0,
            "errors": "",
            "network": _("mainnet"),
            "protocolversion": 1,
            "proxy": "",
            "relayfee": 0.00001,
            "testnet": False,
            "timeoffset": 0,
            "version": 1,
            'current_net': current_net
        }
    }
    return http.JsonResponse(result)

def api_get_currency(request, version):
    """
    """
    result = {"status":200,"data":{"bitstamp":5953.78}}
    return http.JsonResponse(result)

def api_show_blocks(request, version):
    """Show the block list for uri: /blocks

    response
    -------------------
    {
        "blocks":[
            {
                "height":8118,
                "size":201,
                "hash":"00000000086267f5c9cf3d6d44ade95203a3cf713139d98a7b0a3e98947d4ded",
                "time":1508238076,
                "txlength":1,
                "poolInfo":{}
            },],
        "length":200,
        "pagination":{
            "next":"2017-10-18",
            "prev":"2017-10-16",
            "currentTs":1508284799,
            "current":"2017-10-17",
            "isToday":False,
            "more":True,
            "moreTs":1508284800}}
    """
    try:
        # handle the query parameters
        block_date = request.GET.get('blockDate')
        start_ts = request.GET.get('startTimestamp')
        timezone = int(request.GET.get('timezone', 0))
        limit = int(request.GET.get('limit', settings.PAGE_SIZE))
        if limit > settings.PAGE_SIZE:
            limit = settings.PAGE_SIZE
        if block_date:
            block_date = datetime.datetime.strptime(block_date, '%Y-%m-%d')
        else:
            today = datetime.datetime.today()
            block_date = datetime.datetime(today.year, today.month, today.day)
        if start_ts:
            start_ts = int(start_ts)
        else:
            start_ts = 0
        is_today = False
        if block_date == datetime.datetime.today().date():
            is_today = True
        # add given timezone
        # if timezone < 0:
        #     timezone = -timezone
        gmt_date = block_date + datetime.timedelta(hours=timezone)
        next_date = gmt_date + datetime.timedelta(days=1)
        previous_date = gmt_date + datetime.timedelta(days=-1)
        block_ts = gmt_date.timetuple()
        block_ts = int(time.mktime(block_ts))
        next_date_ts = next_date.timetuple()
        next_date_ts = int(time.mktime(next_date_ts))
        # query db
        if start_ts > 0:
            rs = provider_models.Block.objects.filter(time__gte=block_ts, time__lt=start_ts).order_by('-height')
        else:
            rs = provider_models.Block.objects.filter(time__gte=block_ts, time__lt=next_date_ts).order_by('-height')
        cnt = rs.count()
        is_more = False
        more_ts = block_ts
        if cnt > settings.PAGE_SIZE:
            is_more = True
        if cnt > 0:
            rs = rs.limit(limit)
        # output
        blocks = []
        for item in rs:
            item.tx = ''
            t = json.loads(item.to_json())
            # workaround
            t['hash'] = item.id
            validator_name, validator_url = handle_validator(t['validator'])
            t['validator_name'] = validator_name
            t['validator_url'] = validator_url
            blocks.append(t)
        if blocks:
            # get the last timestamp
            more_ts = blocks[-1]['time']
        result = {
            'blocks': blocks,
            'length': len(blocks),
            'pagination': {
                "next": next_date.strftime('%Y-%m-%d'),
                "prev": previous_date.strftime('%Y-%m-%d'),
                "currentTs": block_ts,
                "current": block_date.strftime('%Y-%m-%d'),
                "isToday": is_today,
                "more": is_more,
                "moreTs": more_ts,
            }
        }
        return http.JsonResponse(result)
    except Exception, inst:
        print inst
        logger.exception("fail to show blocks:%s" % str(inst))
        return http.HttpResponseServerError()

def api_show_block_info_by_height(request, version, height):
    """Show the block info by height for uri: /block-index/<height>
    
    """
    try:
        height = int(height)
        obj = provider_models.Block.objects.get(height=height)
        return http.JsonResponse({'blockHash': obj.id})
    except Exception, inst:
        print inst
        logger.exception("fail to show block info by height:%s" % str(inst))
        return http.HttpResponseServerError()
    
def api_show_block_info(request, version, blockhash):
    """Show the block info by block hash key for uri: /block/<hash>

    response
    ------
    {
        "hash":"00000000086267f5c9cf3d6d44ade95203a3cf713139d98a7b0a3e98947d4ded",
        "size":201,
        "height":8118,
        "version":536870912,
        "merkleroot":"bf04109823a6dedda7e07e47b421c36f116cff5b89e13e3c96ab4bfbcad87b33",
        "tx":["bf04109823a6dedda7e07e47b421c36f116cff5b89e13e3c96ab4bfbcad87b33"],
        "time":1508238076,
        "nonce":2073973374,
        "bits":"1c14c83f",
        "difficulty":12.31803921,
        "chainwork":"00000000000000000000000000000000000000000000000000004a1dfddcdea5",
        "confirmations":1,
        "previousblockhash":"000000000b3a33446a9feddc9462312e2fa4f5ba0316672c4b6ab4a37ad90aa4",
        "reward":50,
        "isMainChain":True,
        "poolInfo":{}
    }
    """
    try:
        current_height = provider_services.get_current_height()
        obj = provider_models.Block.objects.get(blockhash=blockhash)
        result = json.loads(obj.to_json())
        result['hash'] = obj.id
        result['isMainChain'] = True
        result['confirmations'] = current_height - obj.height
        result['current_net'] = settings.CURRENT_NET
        validator_name, validator_url = handle_validator(result['validator'])
        result['validator_name'] = validator_name
        result['validator_url'] = validator_url
        return http.JsonResponse(result)
    except Exception, inst:
        print inst
        logger.exception("fail to show block info by hash:%s" % str(inst))
        return http.HttpResponseServerError()


def api_show_transaction_list(request, version):
    """Show the transaction list for uri: /trasactions

    response
    -------------------
    {
        "trans":[
            {
                "txid": "0x9b2e24df970697c1bf7add69711d3114302673bf3e753b975c2bbafaf0b5b3e2"
                "value": 1888
                "time": 1508238076,
            },],
        "length":200,
        "pagination":{
            "next":"2017-10-18",
            "prev":"2017-10-16",
            "currentTs":1508284799,
            "current":"2017-10-17",
            "isToday":False,
            "more":True,
            "moreTs":1508284800}}
    """
    try:
        # handle the query parameters
        trans_date = request.GET.get('transDate')
        start_ts = request.GET.get('startTimestamp')
        timezone = int(request.GET.get('timezone', 0))
        limit = int(request.GET.get('limit', settings.PAGE_SIZE))
        if limit > settings.PAGE_SIZE:
            limit = settings.PAGE_SIZE
        if trans_date:
            trans_date = datetime.datetime.strptime(trans_date, '%Y-%m-%d')
        else:
            today = datetime.datetime.today()
            trans_date = datetime.datetime(today.year, today.month, today.day)
        if start_ts:
            start_ts = int(start_ts)
        else:
            start_ts = 0
        is_today = False
        if trans_date == datetime.datetime.today().date():
            is_today = True
        gmt_date = trans_date + datetime.timedelta(hours=timezone)
        next_date = gmt_date + datetime.timedelta(days=1)
        previous_date = gmt_date + datetime.timedelta(days=-1)
        trans_ts = gmt_date.timetuple()
        trans_ts = int(time.mktime(trans_ts))
        next_date_ts = next_date.timetuple()
        next_date_ts = int(time.mktime(next_date_ts))
        # query db
        if start_ts > 0:
            rs = provider_models.Transaction.objects.filter(time__gte=trans_ts, time__lt=start_ts).order_by('-time')
        else:
            rs = provider_models.Transaction.objects.filter(time__gte=trans_ts, time__lt=next_date_ts).order_by('-time')
        cnt = rs.count()
        is_more = False
        more_ts = trans_ts
        if cnt > settings.PAGE_SIZE:
            is_more = True
        if cnt > 0:
            rs = rs.limit(limit)
        # output
        trans = []
        for items in rs:
            item_dict = dict()
            item_dict['txid'] = items.txid
            item_dict['value'] = float(items.value) / 1000000000000000000
            item_dict['time'] = items.time
            trans.append(item_dict)
        if trans:
            # get the last timestamp
            more_ts = trans[-1]['time']
        result = {
            'trans': trans,
            'length': len(trans),
            'pagination': {
                "next": next_date.strftime('%Y-%m-%d'),
                "prev": previous_date.strftime('%Y-%m-%d'),
                "currentTs": trans_ts,
                "current": trans_date.strftime('%Y-%m-%d'),
                "isToday": is_today,
                "more": is_more,
                "moreTs": more_ts,
            }
        }
        return http.JsonResponse(result)
    except Exception, inst:
        print inst
        logger.exception("fail to show trasactions:%s" % str(inst))
        return http.HttpResponseServerError()


def api_show_transactions(request, version):
    """ show the transcations for uri: /txs

    response
    ------
    {
        "pagesTotal": 1,
        "txs": [
            {
                "blockhash": "0000000009ca522f5611ecf15a46f808394b58b9d811951a5d62f9e94f7e7c81",
                "blockheight": 7642,
                "blocktime": 1508167763,
                "confirmations": 477,
                "isCoinBase": True,
                "locktime": 0,
                "size": 120,
                "time": 1508167763,
                "txid": "fb6b050d695bba36c00097cc74bd4744253e0ca8075dc7361f45c985c98412da",
                "valueOut": 50,
                "version": 1,
                "vin": [
                    {
                        "coinbase": "02da1d00000000006266676d696e657220352e312e302d756e6b6e6f776e0004000000",
                        "n": 0,
                        "sequence": 4294967295
                    },],
                "vout": [
                    {   
                       "n": 0,
                       "scriptPubKey": {
                           "addresses": ["muqq4M9KHTf1kVHWiciLirMybfy22gEA1K"],
                           "asm": "OP_DUP OP_HASH160 9d239fa987bbf55f160fd6cb370be033e4311cbe OP_EQUALVERIFY OP_CHECKSIG",
                           "hex": "76a9149d239fa987bbf55f160fd6cb370be033e4311cbe88ac",
                           "type": "pubkeyhash"
                       },
                       "value": "50.00000000"},]
            },      
        ]
    }
    """
    try:
        tx_type = request.GET.get('type', None)
        has_internal = False
        blockhash = request.GET.get('block')
        addr = request.GET.get('addr')
        contract = request.GET.get('contract')
        if not addr:
            addr = request.GET.get('address')
        if addr:
            addr = addr_translation.b58check_decode(addr)
        page_id = int(request.GET.get('pageNum', 1))
        if page_id > settings.MAX_PAGE_NUM:
            page_id = settings.MAX_PAGE_NUM
        limit = int(request.GET.get('limit', settings.PAGE_SIZE))
        if limit > settings.PAGE_SIZE:
            limit = settings.PAGE_SIZE
        if not addr and contract:
            contract = addr_translation.b58check_decode(contract)
            addr = contract
        total_page = 0
        if blockhash:
            objs = provider_models.Transaction.objects.filter(blockhash=blockhash).max_time_ms(settings.MAX_SELERY_TIME)
            block_obj = provider_models.Block.objects.filter(blockhash=blockhash).first()
            cnt = block_obj.txlength
            if cnt == 0:
                total_page = 1
            else:
                if cnt % settings.PAGE_SIZE != 0:
                    total_page = (cnt / settings.PAGE_SIZE) + 1
                else:
                    total_page = (cnt / settings.PAGE_SIZE)
            objs = objs.skip(page_id * settings.PAGE_SIZE).limit(limit)
        elif addr:
            tx_objs = provider_models.InternalTransaction.objects.filter(to_address=addr).order_by('-time').max_time_ms(
                settings.MAX_SELERY_TIME)
            if tx_objs:
                has_internal = True
            if has_internal and tx_type == 'internal':
                cnt = len(tx_objs)
                if cnt == 0:
                    total_page = 1
                else:
                    if cnt % settings.PAGE_SIZE != 0:
                        total_page = (cnt / settings.PAGE_SIZE) + 1
                    else:
                        total_page = (cnt / settings.PAGE_SIZE)
                objs = tx_objs.skip(page_id * settings.PAGE_SIZE).limit(limit)
            else:
                tx_objs = provider_models.Transaction.objects.filter(Q(from_address=addr) | Q(to_address=addr)).order_by('-time').max_time_ms(settings.MAX_SELERY_TIME)
                account = provider_models.Account.objects.filter(address=addr).first()
                cnt = account.missing_transactions_number + account.transactions_number
                if cnt == 0:
                    total_page = 1
                else:
                    if cnt % settings.PAGE_SIZE != 0:
                        total_page = (cnt / settings.PAGE_SIZE) + 1
                    else:
                        total_page = (cnt / settings.PAGE_SIZE)
                objs = tx_objs.skip(page_id * settings.PAGE_SIZE).limit(limit)
        else:
            raise Exception("invalid parameter")
        txs = []
        current_height = provider_services.get_current_height()
        for obj in objs:
            if has_internal and tx_type == 'internal':
                item = {}
                from_contract_obj = provider_models.Contract.objects.filter(contract_address=obj.contract_address)
                to_contract_obj = provider_models.Contract.objects.filter(contract_address=obj.to_address)
                if from_contract_obj:
                    item['from_contract'] = True
                else:
                    item['from_contract'] = False
                if to_contract_obj:
                    item['to_contract'] = True
                else:
                    item['to_contract'] = False
                item['contract_address'] = addr_translation.address_encode(obj.contract_address)
                item['txid'] = obj.txid
                item['to_address'] = addr_translation.address_encode(obj.to_address)
                item['value'] = Decimal(obj.value) / DECIMAL_SATOSHI
                item['time'] = obj.time
            else:
                item = __convert_transaction_to_json(obj)
                item['confirmations'] = current_height - obj.blockheight
                from_contract = False
                to_contract = False
                from_contract_obj = provider_models.Contract.objects.filter(contract_address=item['from_address'])
                to_contract_obj = provider_models.Contract.objects.filter(contract_address=item['to_address'])
                if from_contract_obj:
                    from_contract = True
                if to_contract_obj:
                    to_contract = True
                item['from_contract'] = from_contract
                item['to_contract'] = to_contract
                from_address = addr_translation.address_encode(item['from_address'])
                to_address = addr_translation.address_encode(item['to_address'])
                item['from_addr'] = from_address
                item['to_addr'] = to_address
                value_issac = item['value']
                value = Decimal(value_issac) / 1000000000000000000
                item['value'] = value
                final_fees = item['fees'] * item['fees_price']
                item['fees'] = final_fees
                item['is_internal'] = False
                res = get_internal_transaction_info(item['txid'])
                if res['is_internal']:
                    item['is_internal_list'] = True
                else:
                    item['is_internal_list'] = False
            txs.append(item)
        result = {
            "pagesTotal": total_page,
            "txs": txs
        }
        return http.JsonResponse(result)
    except Exception, inst:
        print inst
        logger.exception("fail to show transactions:%s" % str(inst))
        return http.HttpResponseServerError()


def get_internal_transaction_info(txid):
    """ get the internal transaction info

    response
    -------
    {
        "is_internal": True,
        "internal_info": [
            {
                "from_contract": True,
                "to_contract": True,
                "contract_address": "NEW17xJKkRcaXhG9G51b5iy8vs37AVsTw9XPgGw",
                "txid": "0x98aea2855d2d37d8a6fb86279da791bd52a619d49eeb43e5d1e2d6141e6da427",
                "to_address": "NEW17xVxeVgdvwZ3Xoc84urTHwKoBVTR3Ai2Fxu",
                "value": Decimal(1),
                "time": 1561466541,
            },
            {
            ...
            },
        ]
    }
    """
    try:
        obj = provider_models.InternalTransaction.objects.filter(txid=txid).all()
        res = {}
        if obj:
            res['is_internal'] = True
            internal_info_list = []
            for ele in obj:
                internal_info = {}
                from_contract_obj = provider_models.Contract.objects.filter(contract_address=ele.contract_address)
                to_contract_obj = provider_models.Contract.objects.filter(contract_address=ele.to_address)
                if from_contract_obj:
                    internal_info['from_contract'] = True
                else:
                    internal_info['from_contract'] = False
                if to_contract_obj:
                    internal_info['to_contract'] = True
                else:
                    internal_info['to_contract'] = False
                internal_info['contract_address'] = addr_translation.address_encode(ele.contract_address)
                internal_info['txid'] = txid
                internal_info['to_address'] = addr_translation.address_encode(ele.to_address)
                internal_info['value'] = Decimal(ele.value) / DECIMAL_SATOSHI
                internal_info['time'] = ele.time
                internal_info_list.append(internal_info)
            res['internal_info'] = internal_info_list
        else:
            res['is_internal'] = False
        return res
    except Exception, inst:
        print inst
        logger.exception("fail to show transactions:%s" % str(inst))
        return http.HttpResponseServerError()


def api_show_transaction(request, version, txid):
    """ show the transcation for uri: /tx

    response
    -------
    {
        "blockhash": "0000000009ca522f5611ecf15a46f808394b58b9d811951a5d62f9e94f7e7c81",
        "blockheight": 7642,
        "blocktime": 1508167763,
        "confirmations": 477,
        "isCoinBase": True,
        "locktime": 0,
        "size": 120,
        "time": 1508167763,
        "txid": "fb6b050d695bba36c00097cc74bd4744253e0ca8075dc7361f45c985c98412da",
        "valueOut": 50,
        "version": 1,
        "vin": [
            {
                "coinbase": "02da1d00000000006266676d696e657220352e312e302d756e6b6e6f776e0004000000",
                "n": 0,
                "sequence": 4294967295
            },
        ],
        "vout": [
            {   
                "n": 0,
                "scriptPubKey": {
                    "addresses": ["muqq4M9KHTf1kVHWiciLirMybfy22gEA1K"],
                    "asm": "OP_DUP OP_HASH160 9d239fa987bbf55f160fd6cb370be033e4311cbe OP_EQUALVERIFY OP_CHECKSIG",
                    "hex": "76a9149d239fa987bbf55f160fd6cb370be033e4311cbe88ac",
                    "type": "pubkeyhash"
                },
                "value": "50.00000000"
            },
        ]
    }
    """
    try:
        obj = provider_models.Transaction.objects.filter(txid=txid).first()
        if obj:
            current_height = provider_services.get_current_height()
            result = __convert_transaction_to_json(obj)
            result['confirmations'] = current_height - obj.blockheight
            from_contract = False
            to_contract = False
            from_contract_obj = provider_models.Contract.objects.filter(contract_address=result['from_address'])
            to_contract_obj = provider_models.Contract.objects.filter(contract_address=result['to_address'])
            if from_contract_obj:
                from_contract = True
            if to_contract_obj:
                to_contract = True
            result['from_contract'] = from_contract
            result['to_contract'] = to_contract
            from_address = addr_translation.address_encode(result['from_address'])
            to_address = addr_translation.address_encode(result['to_address'])
            result['from_addr'] = from_address
            result['to_addr'] = to_address
            value_issac = result['value']
            value = Decimal(value_issac) / 1000000000000000000
            result['value'] = value
            final_fees = result['fees'] * result['fees_price']
            result['fees'] = final_fees
            res = get_internal_transaction_info(txid)
            if res['is_internal']:
                result['is_internal'] = True
                result['internal_info'] = res['internal_info']
            else:
                result['is_internal'] = False
            return http.JsonResponse(result)
        else:
            return http.HttpResponseNotFound()
    except Exception, inst:
        print inst
        logger.exception("fail to show transaction:%s" % str(inst))
        return http.HttpResponseServerError()


def api_show_top_accounts(request, version):
    """ show the accounts ordered by balance descending

    response
    -------
    {
        "total_page": 1,
        "current_page": 1,
        "total_addresses": 210000,
        "total_transactions": 32600,
        "account_list": [
            {
                "rank": 1,
                "address": "NEW17xJKkRcaXhG9G51b5iy8vs37AVsTw9XPgGw",
                "balance": '1000000',
                "txn_count": 273            # the number of transactions
            },
        ]
    }
    """
    try:
        page_id = int(request.GET.get('pageNum', 1))
        res = {}
        # if page_id > settings.MAX_PAGE_NUM:
        #     page_id = settings.MAX_PAGE_NUM
        limit = int(request.GET.get('limit', settings.PAGE_SIZE))
        if limit > settings.PAGE_SIZE:
            limit = settings.PAGE_SIZE
        if ":" in settings.MONGODB_HOST:
            mongo_list = settings.MONGODB_HOST.split(":")            #split MONGODB_HOST to host and port
            client = MongoClient(mongo_list[0], int(mongo_list[1]))
        else:
            client = MongoClient(host=settings.MONGODB_HOST)
        db = client[settings.BLOCK_CHAIN_DB_NAME]
        collection = db['account']
        objs = collection.find({}).collation({"locale": "en", "numericOrdering": True}).sort([("balance", -1), ("transactions_number", -1)])
        # objs = provider_models.Account.objects.order_by('-balance').max_time_ms(settings.MAX_SELERY_TIME)
        if objs:
            cnt = objs.count()
            if cnt == 0:
                total_page = 1
            else:
                if cnt % settings.PAGE_SIZE != 0:
                    total_page = (cnt / settings.PAGE_SIZE) + 1
                else:
                    total_page = (cnt / settings.PAGE_SIZE)
            res['total_page'] = total_page
            if page_id > total_page:
                # raise Exception("page number is too large")
                return http.JsonErrorResponse(error_message='large', data=res)
            else:
                skip_num = (page_id - 1) * settings.PAGE_SIZE
                obj = objs.skip(skip_num).limit(limit)
                account_list = []
                for index, ele in enumerate(obj):
                    account = {}
                    account['rank'] = skip_num + index + 1
                    account['address'] = addr_translation.address_encode(ele['_id'])
                    account['balance'] = Decimal(ele['balance']) / DECIMAL_SATOSHI
                    account['txn_count'] = ele['transactions_number']
                    account_list.append(account)
                res['account_list'] = account_list
                res['current_page'] = page_id
                res['total_addresses'] = cnt
                res['total_transactions'] = provider_models.Transaction.objects.all().count()
        client.close()
        return http.JsonResponse(res)
    except Exception, inst:
        print inst
        logger.exception("fail to show top accounts:%s" % str(inst))
        return http.HttpResponseServerError()


def api_show_addr_summary(request, version, addr):
    """ show the address summary for uri: /addr/<addr>

    response
    -------
    {
    "addrStr": "muqq4M9KHTf1kVHWiciLirMybfy22gEA1K",
    "balance": 381200.0273664,
    "balanceSat": 38120002736640,
    "totalReceived": 409500.029219,
    "totalReceivedSat": 40950002921900,
    "totalSent": 28300.0018526,
    "totalSentSat": 2830000185260,
    "unconfirmedBalance": 0,
    "unconfirmedBalanceSat": 0,
    "unconfirmedTxApperances": 0,
    "txApperances": 8205
    }
    """
    try:
        tx_type = request.GET.get('type', None)
        if tx_type:
            is_internal = True
        else:
            is_internal = False
        eth_addr = addr_translation.b58check_decode(addr)
        internal_list = provider_models.InternalTransaction.objects.filter(to_address=eth_addr)
        if internal_list:
            has_internal = True
        else:
            has_internal = False
        account = provider_models.Account.objects.filter(address=eth_addr).first()
        if account:
            # caculate the txlength
            txlength = account.transactions_number + account.missing_transactions_number
            balance = account.balance
            balanceSat = int(balance) / DECIMAL_SATOSHI
            result = {
                "addrStr": addr,
                "balance": balanceSat,
                "unconfirmedBalance": 0,
                "unconfirmedBalanceSat": 0,
                "unconfirmedTxApperances": 0,
                "txApperances": txlength,
                "is_internal": is_internal,
                "has_internal": has_internal
            }
            return http.JsonResponse(result)
        else:
            return http.HttpResponseNotFound()
    except Exception, inst:
        print inst
        logger.exception("fail to show transaction:%s" % str(inst))
        return http.HttpResponseServerError()

def api_show_transactions_by_addresses(request, version, addrs=None):
    """Show the transaction list of multiple addressed for uri: /addrs/<addrs>/txs

    response
    -------
    """
    try:
        result = {}
        items = []
        no_spent = False
        start_pos = None
        end_pos  = None
        if request.method != 'POST':
            raise Exception("Require POST")
        addrs = request.POST.get('addrs')
        if not addrs:
            try:
                data = json.loads(request.body)
                if data:
                    addrs = data['addrs']
            except:
                pass
        if not addrs:
            logger.error("api_show_transactions_by_addresses:no addrs")
            raise Exception("no addrs")
        # other parameters
        no_spent = True if request.REQUEST.get('noSpent') == "1" else False
        start_pos = request.REQUEST.get('from')
        if start_pos:
            start_pos = int(start_pos)
        end_pos = request.REQUEST.get('to')
        if end_pos:
            end_pos = int(end_pos)
        addrs = addrs.split(',')
        current_height = provider_services.get_current_height()
        for addr in addrs:
            if no_spent:
                rs = provider_models.Transaction.objects.filter(to_address=addr)
            else:
                rs = provider_models.Transaction.objects.filter(Q(from_address=addr) | Q(to_address=addr))
            objs = rs.skip(start_pos).limit(end_pos - start_pos)
            for obj in objs:
                tmp = __convert_transaction_to_json(obj)
                tmp['confirmations'] = current_height - obj.blockheight
                items.append(tmp)
        if start_pos != None and end_pos != None:
            result['from'] = start_pos
            result['to'] = end_pos
        else:
            result['from'] = 0
            result['to'] = len(items)
        result['totalItems'] = len(items)
        result['items'] = items
        return http.JsonResponse(result)
    except Exception, inst:
        print inst
        logger.exception("fail to show transactions by addresses:%s" % str(inst))
        return http.HttpResponseServerError()

def api_send_transcation(request, version):
    """Send transaction for uri: /tx/send

    response
    -------
    """
    try:
        if request.method != "POST":
            raise Exception("Require POST")
        rawtx = request.POST.get('rawtx')
        if not rawtx:
            try:
                data = json.loads(request.body)
                if data:
                    rawtx = data['rawtx']
            except:
                pass
        if not rawtx:
            raise Exception("rawtx is empty.")
        logger.info("api_send_transcation:rawtx:%s" % rawtx)
        txid = provider_services.send_transaction(rawtx)
        if not txid:
            raise Exception("return txid is null")
        return http.JsonResponse({'txid': txid})
    except Exception, inst:
        print inst
        logger.exception("fail to send transaction:%s" % str(inst))
        return http.HttpResponseServerError()

def api_show_newtx(request, version):
    """Show the new transaction for uri: /newtx/

    response
    -------
    """
    try:
        objs = provider_models.Transaction.objects.order_by("-time")[0: 10]
        current_height = provider_services.get_current_height()
        txs = []
        for obj in objs:
            item = __convert_transaction_to_json(obj)
            item['confirmations'] = current_height - obj.blockheight
            value_issac = item['value']
            value = Decimal(value_issac) / 1000000000000000000
            item['value'] = value
            txs.append(item)
        return http.JsonResponse({'txs': txs})
    except Exception, inst:
        print inst
        logger.exception("fail to show new transaction:%s" % str(inst))
        return http.HttpResponseServerError()

def api_show_newblock(request, version):
    """Show the new block for uri: /newblock/

    response
    -------
    """
    try:
        result = {}
        stats = provider_models.Statistics.objects.filter(sync_type=codes.SyncType.SYNC_PROGRAM.value).first()
        if not stats:
            result['height'] = 0
            return http.JsonResponse(result)
        if stats.block_height:
            new_height = stats.block_height
        else:
            new_height = provider_services.get_current_height()
        if new_height:
            result['height'] = new_height
            return http.JsonResponse(result)
        return http.HttpResponseNotFound()
    except Exception, inst:
        print inst
        logger.exception("fail to show new block:%s" % str(inst))
        return http.HttpResponseServerError()

def api_get_estimatefee(request, version):
    """Calculate the translation's fee for url:utils/estimatefee/?nbBlocks=

    response
    -------
    """
    try:
        args = request.GET.get('nbBlocks')
        result = {}
        result[2] = 20000 / 1e8
        if args and len(args) > 0:
            nbBlocks = args.split(",")
            for nbBlock in nbBlocks:
                if int(nbBlock) == 1:
                    result[nbBlock] = 10000 / 1e8
                elif int(nbBlock) == 3:
                    result[nbBlock] = 30000 / 1e8
        return http.JsonResponse(result)
    except Exception, inst:
        return http.HttpResponseServerError()

def api_show_client_transactions(request, version):
    try:
        addr = request.GET.get('addr')
        if not addr:
            addr = request.GET.get('address')
        page_id = int(request.GET.get('pageNum', 1))
        #if page_id > settings.MAX_PAGE_NUM:
        #    page_id = settings.MAX_PAGE_NUM
        limit = int(request.GET.get('limit', settings.PAGE_SIZE))
        if limit > settings.PAGE_SIZE:
            limit = settings.PAGE_SIZE
        total_page = 0
        if addr:
            addr = addr.lower()
            tx_objs = provider_models.Transaction.objects.filter(Q(from_address=addr) | Q(to_address=addr)).order_by('-time').max_time_ms(settings.MAX_SELERY_TIME)
            account = provider_models.Account.objects.filter(address=addr).first()
            if not account:
                result = {
                    "total": 0,
                    "limit": limit,
                    "page": page_id,
                    "pages": 1,
                    "docs": []
                }
                return http.JsonResponse(result)
            cnt = account.transactions_number + account.missing_transactions_number
            if cnt == 0:
                total_page = 1
            else:
                if cnt % limit != 0:
                    total_page = (cnt / limit) + 1
                else:
                    total_page = (cnt / limit)
            objs = tx_objs.skip((page_id - 1) * limit).limit(limit)
        else:
            raise Exception("invalid parameter")
        txs = []
        current_height = provider_services.get_current_height()
        for obj in objs:
            item = __convert_transaction_to_client_json(obj)
            item['confirmations'] = current_height - obj.blockheight
            txs.append(item)
        result = {
            "total": cnt,
            "limit": limit,
            "page": page_id,
            "pages": total_page,
            "docs": txs
        }
        return http.JsonResponse(result)
    except Exception, inst:
        print inst
        logger.exception("fail to show client transactions:%s" % str(inst))
        return http.HttpResponseServerError()

def api_show_client_transaction(request, version):
    try:
        txid = request.GET.get('txid')
        if not txid:
            logger.error("no txid")
            return http.HttpResponseServerError()
        tx = provider_models.Transaction.objects.filter(txid=txid).first()
        if not tx:
            logger.error("no tx")
            return http.HttpResponseServerError()
        current_height = provider_services.get_current_height()
        item = __convert_transaction_to_client_json(tx)
        item['confirmations'] = current_height - tx.blockheight
        result = {
            "tx": item
        }
        return http.JsonResponse(result)
    except Exception, inst:
        logger.exception("fail to show client transaction:%s" % str(inst))
        return http.HttpResponseServerError()

def api_show_contracts_list(request, version):
    try:
        page_id = int(request.GET.get('pageNum', 1))
        limit = int(request.GET.get('limit', settings.PAGE_SIZE))
        if limit > settings.PAGE_SIZE:
            limit = settings.PAGE_SIZE
        contract_objs = provider_models.Contract.objects.order_by('-time')
        statses = provider_models.Statistics.objects.filter()
        cnt = 0
        for stats in statses:
            cnt += stats.contracts_number
        if cnt == 0:
            total_page = 1
        else:
            if cnt % settings.PAGE_SIZE != 0:
                total_page = (cnt / settings.PAGE_SIZE) + 1
            else:
                total_page = (cnt / settings.PAGE_SIZE)
        more = False
        if total_page > 1:
            more = True
        contract_objs = contract_objs.skip((page_id-1) * settings.PAGE_SIZE).limit(limit)
        contract_list = []
        for contract_obj in contract_objs:
            contract = __convert_contract_to_json(contract_obj)
            account_obj = provider_models.Account.objects.filter(address=contract['contract_address']).first()
            if not account_obj:
                continue
            balance_issac = account_obj.balance
            balance = Decimal(balance_issac) / 1000000000000000000
            contract['balance'] = balance
            tx_counts = account_obj.transactions_number + account_obj.missing_transactions_number
            contract['tx_counts'] = tx_counts
            contract['contract_address'] = addr_translation.address_encode(contract['contract_address'])
            contract_list.append(contract)
        result = {
            'contract_list': contract_list,
            'pagination': total_page,
            'is_more': more
        }
        return http.JsonResponse(result)
    except Exception, inst:
        logger.exception("fail to show contract list:%s" % str(inst))
        return http.HttpResponseServerError()

def api_show_contract(request, version, contractAddr):
    try:
        contractAddr = addr_translation.b58check_decode(contractAddr)
        contract_obj = provider_models.Contract.objects.filter(contract_address=contractAddr).first()
        if contract_obj:
            contract = __convert_contract_to_json(contract_obj)
        else:
            raise Exception("contract does not exist!")
        account_obj = provider_models.Account.objects.filter(address=contract['contract_address']).first()
        balance_issac = account_obj.balance
        balance = Decimal(balance_issac) / 1000000000000000000
        contract['balance'] = balance
        tx_counts = account_obj.transactions_number + account_obj.missing_transactions_number
        contract['tx_counts'] = tx_counts
        contract['contract_address'] = addr_translation.address_encode(contract['contract_address'])
        contract['creator'] = addr_translation.address_encode(contract['creator'])
        result = {
            'contract': contract
        }
        return http.JsonResponse(result)
    except Exception, inst:
        logger.exception("fail to show contract:%s" % str(inst))
        return http.HttpResponseServerError()

def api_for_dashboard(request):
    try:
        sync_stats = provider_models.Statistics.objects.filter(sync_type=codes.SyncType.SYNC_PROGRAM.value).first()
        if not sync_stats:
            result = {
                'current_height': 0,
                'total_transactions': 0,
                'tps': 0,
                'tx': 0
            }
            return http.JsonResponse(result)
        current_height = sync_stats.block_height
        fill_stats = provider_models.Statistics.objects.filter(sync_type=codes.SyncType.FILL_MISSING_PROGRAM.value).first()
        if fill_stats:
            total_transactions = sync_stats.transactions_number + fill_stats.transactions_number
        else:
            total_transactions = sync_stats.transactions_number
        current_block = provider_models.Block.objects.order_by('-time')[0]
        tps = int(current_block.txlength) / 3
        tx = {}
        time = current_block.time
        tx[time] = current_block.txlength
        result = {
            'current_height': current_height,
            'total_transactions': total_transactions,
            'tps': tps,
            'tx': tx
        }
        return http.JsonResponse(result)
    except Exception, inst:
        logger.exception("fail to show dashboard data:%s" % str(inst))
        return http.HttpResponseServerError()

def api_home_brief(request, version):
    try:
        fill_stats = provider_models.Statistics.objects.filter(sync_type=codes.SyncType.FILL_MISSING_PROGRAM.value).first()
        sync_stats = provider_models.Statistics.objects.filter(sync_type=codes.SyncType.SYNC_PROGRAM.value).first()
        if not sync_stats:
            result = {
                'blocks': 0,
                'transactions': 0,
                'contracts': 0
            }
            return http.JsonResponse(result)
        current_height = sync_stats.block_height
        if fill_stats:
            total_transactions = sync_stats.transactions_number + fill_stats.transactions_number
            contracts = sync_stats.contracts_number + fill_stats.contracts_number
        else:
            total_transactions = sync_stats.transactions_number
            contracts = sync_stats.contracts_number
        result = {
            'blocks': current_height,
            'transactions': total_transactions,
            'contracts': contracts
        }
        return http.JsonResponse(result)
    except Exception, inst:
        logger.exception("fail to get home page brief:%s" % str(inst))
        return http.HttpResponseServerError()

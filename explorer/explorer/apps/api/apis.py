# -*- coding: utf-8 -*-
__author__ = 'xiawu@xiawu.org'
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
DECIMAL_SATOSHI = Decimal("100000000")


logger = logging.getLogger(__name__)

# internal utils functions

def __convert_transaction_to_json(obj):
    result = json.loads(obj.to_json())
    result['id'] = obj.id
    result['operations'] = []
    result['contract']= None
    result['blockNumber'] = obj.blockheight
    result['timeStamp'] = obj.time
    result['nonce'] = 0
    result['from'] = obj.from_address
    result['to'] = obj.to_address 
    result['value'] = obj.value
    result['input'] = obj.data
    result['gas'] = obj.fees
    result['gasPrice'] = obj.fees_price
    result['_id'] = obj.id
    result['error'] = ""
    result['gasUsed'] = obj.fees/obj.fees_price
    return result

def __convert_num_to_float(num):
    res = float(Decimal(str(num)) * DECIMAL_SATOSHI / DECIMAL_SATOSHI)
    return res

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
            "type": _("newton node"),
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
            "version": 1
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

        if timezone < 0:
            timezone = 24 + timezone
        block_date = block_date + datetime.timedelta(hours=timezone)
        next_date = block_date + datetime.timedelta(days=1)
        previous_date = block_date + datetime.timedelta(days=-1)
        block_ts = block_date.timetuple()  
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
            rs = rs[:limit]
        # output
        blocks = []
        for item in rs:
            t = json.loads(item.to_json())
            # workaround
            t['hash'] = item.id
            blocks.append(t)
        if blocks:
            # get the last timestamp
            more_ts = blocks[-1]['time']
        # add the total number of transactions
        number_of_transactions = provider_models.Transaction.objects.filter().count()
        result = {
            'blocks': blocks,
            'number_of_transactions': number_of_transactions,
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
        return http.JsonResponse(result)
    except Exception, inst:
        print inst
        logger.exception("fail to show block info by hash:%s" % str(inst))
        return http.HttpResponseServerError()

def api_show_transcations(request, version):
    """ show the transcations for uri: /txs

    response
    ------
    {
        "docs": [
            {
            "operations": [
                
            ],
            "contract": null,
            "_id": "0xe829a33c3e025c0aa1d81ad99a56be7598ff655feecad99962f167c230e1f48f",
            "blockNumber": 7339862,
            "timeStamp": "1526637504",
            "nonce": 20127,
            "from": "0x003bbce1eac59b406dd0e143e856542df3659075",
            "to": "0x782c7147fbf339660d74f407832e0fecf4d49d31",
            "value": "5000000000000000000",
            "gas": "100000",
            "gasPrice": "14959965017",
            "gasUsed": "21000",
            "input": "0x",
            "error": "",
            "id": "0xe829a33c3e025c0aa1d81ad99a56be7598ff655feecad99962f167c230e1f48f"
            }
        ],
        "total": 1,
        "limit": 50,
        "page": 1,
        "pages": 1
    }
    """
    try:
        blockhash = request.GET.get('block')
        addr = request.GET.get('addr')
        if not addr:
            addr = request.GET.get('address')
        page_id = int(request.GET.get('pageNum', 1))
        limit = int(request.GET.get('limit', settings.PAGE_SIZE))
        total_page = 0
        if blockhash:
            objs = provider_models.Transaction.objects.filter(blockhash=blockhash)
            cnt = objs.count()
            if cnt == 0:
                total_page = 1
            else:
                if cnt % settings.PAGE_SIZE != 0:
                    total_page = (cnt / settings.PAGE_SIZE) + 1
                else:
                    total_page = (cnt / settings.PAGE_SIZE)
            objs = objs.skip(page_id * settings.PAGE_SIZE).limit(limit)
        elif addr:
            txids = provider_models.Address.objects.filter(addr=addr).distinct('txid')
            cnt = len(txids)
            if cnt == 0:
                total_page = 1
            else:
                if cnt % settings.PAGE_SIZE != 0:
                    total_page = (cnt / settings.PAGE_SIZE) + 1
                else:
                    total_page = (cnt / settings.PAGE_SIZE)
            objs = provider_models.Transaction.objects.filter(txid__in=txids).order_by('-time')
            objs = objs.skip(page_id * settings.PAGE_SIZE).limit(limit)
        else:
            raise Exception("invalid parameter")
        txs = []
        current_height = provider_services.get_current_height()
        for obj in objs:
            item = __convert_transaction_to_json(obj)
            item['confirmations'] = current_height - obj.blockheight
            txs.append(item)
        result = {
            "total": cnt,
            "limit": settings.PAGE_SIZE,
            "page": page_id,
            "pages": total_page,
            "docs": txs
        }
        return http.JsonResponse(result)
    except Exception, inst:
        print inst
        logger.exception("fail to show transactions:%s" % str(inst))
        return http.HttpResponseServerError()

def api_show_transcation(request, version, txid):
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
            return http.JsonResponse(result)
        else:
            return http.HttpResponseNotFound()
    except Exception, inst:
        print inst
        logger.exception("fail to show transaction:%s" % str(inst))
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
        obj = provider_models.Address.objects.filter(addr=addr).first()
        if obj:
            total_received = provider_models.Address.objects.filter(addr=addr, vtype=codes.ValueType.RECEIVE.value).sum('value')
            total_sent = provider_models.Address.objects.filter(addr=addr, vtype=codes.ValueType.SEND.value).sum('value')
            balance = total_received - total_sent
            txlength = len(provider_models.Address.objects.filter(addr=addr).distinct('txid'))
            balance = __convert_num_to_float(balance)
            total_received = __convert_num_to_float(total_received)
            total_sent = __convert_num_to_float(total_sent)
            balanceSat = int(float(balance) * settings.UNIT_TO_SATOSHI)
            totalReceivedSat = int(float(total_received) * settings.UNIT_TO_SATOSHI)
            totalSentSat = int(float(total_sent) * settings.UNIT_TO_SATOSHI)
            result = {
                "addrStr": addr,
                "balance": balance,
                "balanceSat": balanceSat,
                "totalReceived": total_received,
                "totalReceivedSat": totalReceivedSat,
                "totalSent": total_sent,
                "totalSentSat": totalSentSat,
                "unconfirmedBalance": 0,
                "unconfirmedBalanceSat": 0,
                "unconfirmedTxApperances": 0,
                "txApperances": txlength
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
                txids = provider_models.Address.objects.filter(addr=addr, vtype=codes.ValueType.RECEIVE.value).distinct('txid')
            else:
                txids = provider_models.Address.objects.filter(addr=addr).distinct('txid')
            objs = provider_models.Transaction.objects.filter(txid__in=txids)
            for obj in objs:
                tmp = __convert_transaction_to_json(obj)
                tmp['confirmations'] = current_height - obj.blockheight
                items.append(tmp)
        items = sorted(items, key=lambda x:x['blockheight'], reverse=True)
        if start_pos != None and end_pos != None:
            items = items[start_pos:end_pos]
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
        result = provider_services.get_transaction_pool()
        return http.JsonResponse(result)
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
        height = int(request.GET.get('height', 0))
        new_height = provider_services.get_current_height()
        if height == 0:
            height = new_height
        if new_height >= height:
            newblock_hash = provider_services.get_block_hash_by_height(height)
            if newblock_hash:
                result['hash'] = newblock_hash
                result['height'] = height
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


def api_richest_list(request, version):
    """ show the richest list for uri: /addrs/richest-list 
    """ 
    # vtype RECEIVE = 1, SEND = 2 
    # response
    # -------
    # [
    # {
    # percentage: 0.45,
    # balance: 14999999.999999,
    # address: "8KNrJAyF4M67HT5tma7ZE4Rx9N9YzaUbtM"
    # },
    # {
    # percentage: 0.15,
    # balance: 5000000,
    # address: "8K9gkit8NPM5bD84wJuE5n7tS9Rdski5uB"
    # },
    # {
    # percentage: 0.1,
    # balance: 3338576.362979,
    # address: "8S7jTjYjqBhJpS9DxaZEbBLfAhvvyGypKx"
    # },
    # ...
    # ]
    # addr_list = provider_models.Address.objects.filter().distinct('addr')
    # for addr in addr_list:
    #     total_received = provider_models.Address.objects.filter(addr=addr, vtype=codes.ValueType.RECEIVE.value).sum('value')
    #     total_sent = provider_models.Address.objects.filter(addr=addr, vtype=codes.ValueType.SEND.value).sum('value')
    #     print total_received

    info = []
    balance_list = provider_models.Balance.objects.filter()
    richest_list = balance_list.order_by("-value").limit(100)
    sum_balance = balance_list.sum('value')
    for rl in richest_list:
        balance = {}
        balance['address'] = rl['addr']
        balance['balance'] = round(__convert_num_to_float(rl['value']), 6)
        balance['percentage'] = round((rl['value'] / sum_balance) * 100, 5)
        info.append(balance)
    result = {
        "info": info
    }
    
    return http.JsonResponse(result)



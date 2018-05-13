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
    result['txid'] = obj.id
    result['blocktime'] = obj.time
    result['fees'] = __convert_num_to_float(obj.fees)
    vouts = obj['vout']
    for v in vouts:
        v['value'] = __convert_num_to_float(v['value'])
    result['vout'] = vouts
    result['valueOut'] = __convert_num_to_float(obj['valueOut'])
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
            "pagesTotal": total_page,
            "txs": txs
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

def api_show_utxo_by_address(request, version, addr):
    """Show the utxo list of one address for uri: /addr/<addr>/utxo

    response
    -------
    {
    "address":"mo9ncXisMeAoXwqcV5EWuyncbmCcQN4rVs",
    "txid":"d5f8a96faccf79d4c087fa217627bb1120e83f8ea1a7d84b1de4277ead9bbac1",
    "vout":0,
    "scriptPubKey":"76a91453c0307d6851aa0ce7825ba883c6bd9ad242b48688ac",
    "amount":0.000006,
    "satoshis":600,
    "confirmations":0,
    "ts":1461349425
    }
    
    single to single
    [
    {
        "txid": "f90716ff9f9c559f9ac7c8063a8c94aba17a7b2b56be4e47183935c0e590627d",
        "vout": 1,
        "address": "n2Wp2pQcickmvLDsHQSVD1ZFsRUnbFPBv5",
        "scriptPubKey": "76a914e653be7e5d3f97c2fe2557a0d07fcf86d97a2c2588ac",
        "satoshis": 100000000,
        "confirmations": 3,
        "locked": false,
        "path": "m/0/0",
        "publicKeys": [
            "03f13dcf3415ef6da974ace3f8b6fbf5e9acb51c6077db9e78fb6fe89ee00a62e3"
        ]
    }
    ]
    single to multiple
    [
    {
        "txid": "d46ef1d4605f435732371a9e38e54a189a931e40850fab6030069ebb9eba5e9f",
        "vout": 1,
        "address": "2MtiHiAyi52vMBrN94ScMmJ8KF7uwgHJqE8",
        "scriptPubKey": "a914101676c29892012870358153d3c0fada14f296ab87",
        "satoshis": 50000000,
        "confirmations": 0,
        "locked": false,
        "path": "m/0/0",
        "publicKeys": [
            "023fa0de3b66e10e9077981612d5b48963ae66c3d505d227ab5646f4c2c26ab6b0",
            "02c16a7ce63bc672ded353edead1325414f5db8256f9a31b9b5b0669adcb9360a2",
            "02d324b252a01c03a02cd5edc1df9cfdf1a34da8280f634f1a4b1de81b568f217f"
        ]
    }
    ]
    multiple to multiple
    [
    {
        "txid": "99468ddc6327a8596e8e5e952bccc6f78582ec923881a3aa678cbe0f34c19e28",
        "vout": 0,
        "address": "2N7YR6ZA5cufV4m6jUCHjo6d87YpC2mEbj4",
        "scriptPubKey": "a9149cd21adc034c173548e50268cc76c59730a1513d87",
        "satoshis": 10000000,
        "confirmations": 0,
        "locked": false,
        "path": "m/0/1",
        "publicKeys": [
            "03b37db2a0ea113956d9861518f77f593bc2b0eb509163f16312128606a6146d28",
            "023fba8d654175d9953df8402be331b8821e5e1f5daadf2e4334e3bba095853035",
            "024a348cf02fc085a3c12db29fadc98e201d4dfd89b3f161fef94661b1c269fbd3"
        ]
    },
    {
        "txid": "d46ef1d4605f435732371a9e38e54a189a931e40850fab6030069ebb9eba5e9f",
        "vout": 1,
        "address": "2MtiHiAyi52vMBrN94ScMmJ8KF7uwgHJqE8",
        "scriptPubKey": "a914101676c29892012870358153d3c0fada14f296ab87",
        "satoshis": 50000000,
        "confirmations": 3,
        "locked": true,
        "path": "m/0/0",
        "publicKeys": [
            "023fa0de3b66e10e9077981612d5b48963ae66c3d505d227ab5646f4c2c26ab6b0",
            "02c16a7ce63bc672ded353edead1325414f5db8256f9a31b9b5b0669adcb9360a2",
            "02d324b252a01c03a02cd5edc1df9cfdf1a34da8280f634f1a4b1de81b568f217f"
        ]
    }
]
multiple to single
[
    {
        "txid": "0afa10a03c6086425c48f4d0801dc45ade917953cb9d9f5b32770e6acf4dc24d",
        "vout": 0,
        "address": "mkQgTEHmsZKjq4S4KRQB2v5RWu9Tas5Gw9",
        "scriptPubKey": "76a91435a8e8b9bbe0af952bd1495fd9c8e2819f2934b788ac",
        "satoshis": 10000000,
        "confirmations": 0,
        "locked": false,
        "path": "m/0/1",
        "publicKeys": [
            "02c89b5cc52d9beef879d333d8c87ab41789e0e970b2913549c1c7c7e29503a033"
        ]
    },
    {
        "txid": "50ba285d80f83dd63c588598a3a025d3200814006dfb92d95a419528cea28ecb",
        "vout": 1,
        "address": "mqcep7iQKbbsJLzRarvV2mcNP7YWL3tvcG",
        "scriptPubKey": "76a9146ec5291f7e9e6954df6f64633565f20373450d2e88ac",
        "satoshis": 49980560,
        "confirmations": 6,
        "locked": false,
        "path": "m/1/0",
        "publicKeys": [
            "0350c30246dc41600c1dc4eaa8b3caee044f584e963574f2fb83b1752b3703e242"
        ]
    }
]

    """
    try:
        result = provider_services.get_utxo_by_address(addr)
        return http.JsonResponse(result)
    except Exception, inst:
        print inst
        logger.exception("fail to show utxo by address:%s" % str(inst))
        return http.HttpResponseServerError()

def api_show_utxo_by_addresses(request, version, addrs=None):
    """Show the utxo list of multiple addressed for uri: /addrs/<addrs>/utxo

    response
    -------
    {
    "address":"mo9ncXisMeAoXwqcV5EWuyncbmCcQN4rVs",
    "txid":"d5f8a96faccf79d4c087fa217627bb1120e83f8ea1a7d84b1de4277ead9bbac1",
    "vout":0,
    "scriptPubKey":"76a91453c0307d6851aa0ce7825ba883c6bd9ad242b48688ac",
    "amount":0.000006,
    "satoshis":600,
    "confirmations":0,
    "ts":1461349425
    }
    """
    try:
        result = []
        addrs = None
        if request.method != 'POST':
            raise Exception('Require POST')
        addrs = request.POST.get('addrs')
        if not addrs: # find json format
            try:
                data = json.loads(request.body)
                if data:
                    addrs = data['addrs']
            except:
                pass
        if addrs:
            addrs = addrs.split(',')
            tmp = provider_services.get_utxo_by_address(addrs)
            if tmp:
                result.extend(tmp)
        return http.JsonResponse(result)
    except Exception, inst:
        print inst
        logger.exception("fail to show utxo by addresses:%s" % str(inst))
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



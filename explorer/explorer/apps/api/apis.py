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
DECIMAL_SATOSHI = Decimal("1000000000000000000")
from utils import newchain_tools
import datetime
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
        # add the total number of transactions
        # number_of_transactions = provider_models.Transaction.objects.filter().count()
        result = {
            'blocks': blocks,
            # 'number_of_transactions': number_of_transactions,
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
        cache_info = cache.get(blockhash)
        if cache_info:
            return http.JsonResponse(cache_info)
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
        cache.set(blockhash, result, 7200)
        return http.JsonResponse(result)
    except Exception, inst:
        print inst
        logger.exception("fail to show block info by hash:%s" % str(inst))
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
        blockhash = request.GET.get('block')
        addr = request.GET.get('addr')
        contract = request.GET.get('contract')
        if not addr:
            addr = request.GET.get('address')
        if addr:
            addr = addr_translation.b58check_decode(addr)
        page_id = int(request.GET.get('pageNum', 1))
        limit = int(request.GET.get('limit', settings.PAGE_SIZE))
        if not addr and contract:
            contract = addr_translation.b58check_decode(contract)
            addr = contract
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
            addr_objs = provider_models.Address.objects.filter(address=addr).order_by('-time')
            cnt = addr_objs.count()
            if cnt == 0:
                total_page = 1
            else:
                if cnt % settings.PAGE_SIZE != 0:
                    total_page = (cnt / settings.PAGE_SIZE) + 1
                else:
                    total_page = (cnt / settings.PAGE_SIZE)
            addr_objs = addr_objs.skip(page_id * settings.PAGE_SIZE).limit(limit)
            txid_list = []
            for addr_obj in addr_objs:
                txid = addr_obj.txid
                txid_list.append(txid)
            objs = provider_models.Transaction.objects.filter(txid__in=txid_list).order_by('-time')
        else:
            raise Exception("invalid parameter")
        txs = []
        current_height = provider_services.get_current_height()
        for obj in objs:
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
        cache_info = cache.get(txid)
        if cache_info:
            return http.JsonResponse(cache_info)
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
            cache.set(txid, result, 7200)
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
        eth_addr = addr_translation.b58check_decode(addr)
        obj = provider_models.Account.objects.filter(address=eth_addr)
        if obj:
            res = __convert_account_to_json(obj)
            # caculate the txlength
            txlength = provider_models.Address.objects.filter(address=eth_addr).count()
            balance = res[0]['balance']
            balanceSat = int(balance) / DECIMAL_SATOSHI
            result = {
                "addrStr": addr,
                "balance": balanceSat,
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
        new_tx = cache.get('new_tx')
        if new_tx:
            return http.JsonResponse({'txs': new_tx})
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
        cache.set('new_tx', txs, 20)
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
        new_blocks = cache.get('new_blocks')
        if new_blocks:
            logger.info('new_blocks:%s' % new_blocks)
            return http.JsonResponse(new_blocks)
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
                cache.set('new_blocks', result, 20)
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
        limit = int(request.GET.get('limit', settings.PAGE_SIZE))
        total_page = 0
        if addr:
            addr = addr.lower()
            rs = provider_models.Address.objects.filter(address=addr).order_by('-time')
            cnt = rs.count()
            if cnt == 0:
                total_page = 1
            else:
                if cnt % limit != 0:
                    total_page = (cnt / limit) + 1
                else:
                    total_page = (cnt / limit)
            addr_objs = rs.skip((page_id - 1) * limit).limit(limit)
            txid_list = []
            for addr_obj in addr_objs:
                txid = addr_obj.txid
                txid_list.append(txid)
            objs = provider_models.Transaction.objects.filter(txid__in=txid_list).order_by('-time')
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
        contract_objs = provider_models.Contract.objects.order_by('-time')
        cnt = contract_objs.count()
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
            balance_issac = account_obj.balance
            balance = Decimal(balance_issac) / 1000000000000000000
            contract['balance'] = balance
            tx_counts = provider_models.Address.objects.filter(address=contract['contract_address']).count()
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
        tx_counts = provider_models.Address.objects.filter(address=contract['contract_address']).count()
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
        current_height = provider_services.get_current_height()
        total_transactions = provider_models.Transaction.objects.filter().count()
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
        cache_info = cache.get('brief_data')
        if cache_info:
            logger.info('brief_data:%s' % cache_info)
            return http.JsonResponse(cache_info)
        current_height = provider_services.get_current_height()
        total_transactions = provider_models.Transaction.objects.filter().count()
        contracts = provider_models.Contract.objects.filter().count()
        result = {
            'blocks': current_height,
            'transactions': total_transactions,
            'contracts': contracts
        }
        cache.set('brief_data', result, 20)
        return http.JsonResponse(result)
    except Exception, inst:
        logger.exception("fail to get home page brief:%s" % str(inst))
        return http.HttpResponseServerError()
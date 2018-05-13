"""The blockchain service implementation of newton node 

"""

__copyright__ = """ Copyright (c) 2016 Beijing ShenJiangHuDong Technology Co., Ltd. All rights reserved."""
__version__ = '1.0'
__author__ = 'xiawu@lubangame.com'

import logging
import json
import requests
import copy
from decimal import *

logger = logging.getLogger(__name__)
COINBASE_TXID = '0' * 64
DECIMAL_SATOSHI = Decimal("100000000")

class Provider(object):
    def __init__(self, url_prefix):
        self.url_prefix = url_prefix
        self.headers = {'content-type': 'application/json'}

    def _get(self, uri, params):
        url = '%s%s' % (self.url_prefix, uri)
        logger.debug(url)
        response = requests.get(url, data=json.dumps(params), headers=self.headers)
        response = response.json()
        if response['Error'] != 0:
            logger.error("_get: url:%s, params:%s, return:%s" % (url, params, response))
            raise Exception("%s:error-%s,desc-%s" % (response['Action'], response['Error'], response['Desc']))
        logger.debug(response)
        return response

    def _post(self, uri, params):
        url = '%s%s' % (self.url_prefix, uri)
        response = requests.post(url, data=json.dumps(params), headers=self.headers)
        response = response.json()
        if response['Error'] != 0:
            logger.error("_post: url:%s, params:%s, return:%s" % (url, params, response))
            raise Exception("%s:error-%s,desc-%s" % (response['Action'], response['Error'], response['Desc']))
        logger.debug(response)
        return response
    
    def get_block_height(self):
        response = self._get('/block/height', {})
        return response['Result']

    def parse_block_info(self, result):
        # convert to uniform format
        final_result = {
            'blockhash': result['Hash'],
            'previousblockhash': result['BlockData']['PrevBlockHash'],
            'version': result['BlockData']['Version'],
            'height': result['BlockData']['Height'],
            'merkleroot': result['BlockData']['TransactionsRoot'],
            'time': result['BlockData']['Timestamp'],
            'confirmations': result['Confirmations'],
            #'nonce': result['BlockData']['AuxPow']['Nonce'],
            'nonce': 0,
            'bits': result['BlockData']['Bits'],
            #'difficulty': result['BlockData']['Difficulty'],
            'difficulty': '0',
            #'size': result['BlockData']['BlockSize'],
            'size': 0,
            'poolInfo': {'poolName': result['MinerInfo'], 'url':''},
        }
        tx = []
        tx_detail = []
        for item in result['Transactions']:
            obj = self.parse_transaction_response(item)
            if obj:
                tx_detail.append(obj)
                tx.append(item['Hash'])
        final_result['tx'] = tx
        final_result['tx_detail'] = tx_detail
        final_result['txlength'] = len(tx)
        return final_result

    def get_block_by_height(self, height):
        response = self._get('/block/details/height/%s' % height, {'height': height})
        result = response['Result']
        return self.parse_block_info(result)

    def get_block_by_hash(self, hash_key):
        response = self._get('/block/details/hash/%s' % hash_key, {'hash': hash_key})
        result = response['Result']
        return self.parse_block_info(result)

    def __reverse_hash(self, hash_key):
        cnt = 0
        result = ''
        hash_key = hash_key[::-1]
        for i in hash_key:
            if cnt % 2 == 0:
                result += '%s%s' % (hash_key[cnt + 1], i)
            cnt += 1
        return result

    def parse_transaction_response(self, response):
        tx_type = response.get('TxType', 0)
        if tx_type not in [0, 2]:
            return None
        final_result = {
            'txid': response['Hash'],
        }
        final_result['version'] = 0
        final_result['vin'] = []
        final_result['isCoinBase'] = False
        final_result['size'] = response.get('TxSize', 0)
        final_result['time'] = response.get('Timestamp', 0)
        final_result['confirmations'] = response.get('Confirmations', 0)
        final_result['locktime'] = response.get('LockTime', 0)
        value_in = 0
        for item in response['UTXOInputs']:
            n = item['ReferTxOutputIndex']
            txid = item['ReferTxID']
            addr = item['Address']
            # check it is a coinbase transaction
            if addr:
                value = Decimal(item['Value'])
                final_result['vin'].append({'n': n, 'txid': txid, 'addr': addr, 'value': float(value), 'valueSat': int(value * DECIMAL_SATOSHI)})
                value_in += int(value * DECIMAL_SATOSHI)
            else:
                final_result['vin'].append({'n': n, 'coinbase': txid, 'sequence': item['Sequence']})
                final_result['isCoinBase'] = True
        final_result['vout'] = []
        cnt = 0
        value_out = 0
        for item in response['Outputs']:
            value = Decimal(item['Value'])
            final_result['vout'].append({'n': cnt, 'value': float(value), 'valueSat': int( value * DECIMAL_SATOSHI), 'scriptPubKey': {'addresses': [item['Address']], 'type': 'pubkeyhash'}})
            value_out += int(value * DECIMAL_SATOSHI)
            cnt += 1
        final_result['valueOut'] = float(Decimal(str(value_out)) / DECIMAL_SATOSHI)
        fees = 0
        if value_in > value_out:
            fees = value_in - value_out
        final_result['fees'] = float(Decimal(str(fees)) / DECIMAL_SATOSHI)
        return final_result

    def get_transaction_by_hash(self, hash_key):
        new_hash_key = copy.deepcopy(hash_key)
        response = self._get('/transaction/%s' % new_hash_key, {'hash': new_hash_key})
        result = response['Result']
        # convert to uniform format
        return self.parse_transaction_response(result)

    def __get_addr_and_value_for_transaction(self, n, txid):
        """# TODO: remove it when onchain api is OK
        """
        new_txid = copy.deepcopy(txid)
        response = self._get('/transaction/%s' % new_txid, {'hash': new_txid})
        result = response['Result']
        cnt = 0
        for item in result['Outputs']:
            if cnt == n:
                addr =  item['Address']
                value = item['Value']
                return addr, value
            cnt += 1
        return "", 0

    def get_utxo_by_address(self, address):
        from django.conf import settings
        
        response = self._get('/asset/utxos/%s' % address, {'addr': address})
        result = response['Result']
        final_result = []
        if result:
            utxo = result[0]['Utxo']
            if utxo:
                for item in utxo:
                    value = float(item['Value'])
                    satoshis = int(value * settings.UNIT_TO_SATOSHI)
                    txid = item['Txid']
                    vout = item['Index']
                    final_result.append({'address': address, 'vout': vout, 'amount': value, 'satoshis': satoshis, 'confirmations':10, 'ts':0, 'txid': txid, 'scriptPubKey': ''})
        return final_result

    def get_balance_by_address(self, address):
        response = self._get('/asset/balances/%s' % address, {'addr': address})
        result = response['Result']
        return result

    def send_transaction(self, rawtx):
        response = self._post('/transaction', {'Data': rawtx, 'Type': 0x10, 'Action': 'sendrawtransaction'})
        result = response['Result']
        return result

    def get_transaction_pool(self):
        """Get the temporary transaction list of transaction pool
        """
        response = self._get('/transactionpool', {})
        final_result = []
        for item in response['Result']:
            tmp = self.parse_transaction_response(item)
            if tmp:
                final_result.append(tmp)
        return final_result

if __name__ == '__main__':
    url_prefix= ''
    provider = Provider(url_prefix)
    # get block height
    print provider.get_block_height()
    # get block by height
    print provider.get_block_by_height(200)
    # get block by hash
    print provider.get_block_by_hash('00000049fcf2a51594829c42564745e52c5559aed19fff458f331d94eda6834c')
    # get transaction by hash
    print provider.get_transaction_by_hash('736fc7da431878b59691ebaf3cb2a1685eac4a900b9989aa068fdfb7cb49408e')
    # get utxos by address
    print provider.get_utxo_by_address('Aa4z5yUtTvAwS5CKLb2U7yHpeAk9zCikHM')
    # get balance by address
    print provider.get_balance_by_address('Aa4z5yUtTvAwS5CKLb2U7yHpeAk9zCikHM')

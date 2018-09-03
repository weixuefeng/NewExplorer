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
from ctypes import *
import os

logger = logging.getLogger(__name__)
COINBASE_TXID = '0' * 64
DECIMAL_SATOSHI = Decimal("100000000")


class Provider(object):
    def __init__(self, url):
        self.url = url
        self.headers = {'content-type': 'application/json'}
        self.payload = {
            "jsonrpc": "2.0",
            "id": 0,
        }

    def _post(self, method, params):
        payload = copy.deepcopy(self.payload)
        payload['method'] = method
        payload['params'] = params
        response = requests.post(self.url, data=json.dumps(payload), headers=self.headers)
        response = response.json()
        return response

    def get_block_height(self):
        response = self._post('eth_blockNumber', [])
        return int(response['result'], 0)

    def parse_block_info(self, result):
        # convert to uniform format
        if not result:
            return None
        transactions = result['transactions']
        final_result = {
            'blockhash': result['hash'],
            'previousblockhash': result['parentHash'],
            'height': long(result['number'], 0),
            'time': long(result['timestamp'], 0),
            'size': long(result['size'], 0),
            'nonce': result['nonce'],
            'tx': [],
            'transactions': transactions,
        }
        for item in transactions:
            final_result['tx'].append(item['hash'])
        final_result['txlength'] = len(final_result['tx'])
        return final_result

    def get_block_by_height(self, height):
        response = self._post('eth_getBlockByNumber', ['0x%x' % height, True])
        result = response.get('result')
        validator_lib = self.load_validator_lib()
        validator_address = self.get_validator(validator_lib, result)
        final_result = self.parse_block_info(result)
        final_result['validator'] = validator_address
        return final_result

    def get_block_by_hash(self, hash_key):
        response = self._post('eth_getBlockByHash', [hash_key, True])
        result = response['result']
        return self.parse_block_info(result)

    def get_transaction_count_by_height(self, height):
        response = self._post('eth_getBlockTransactionCountByNumber', ['0x%x' % height])
        result = response['result']
        return int(result, 0)

    def get_transaction_by_height_and_index(self, height, index):
        response = self._post('eth_getTransactionByBlockNumberAndIndex', ['0x%x' % height, '0x%x' % index])
        result = response['result']
        return self.parse_transaction_response(result)

    def parse_transaction_response(self, response):
        final_result = {
            'txid': response['hash'],
        }
        final_result['from_address'] = response['from']
        final_result['to_address'] = response['to']
        final_result['value'] = str(long(response['value'], 0))
        final_result['fees'] = long(response['gas'], 0)
        final_result['fees_price'] = long(response['gasPrice'], 0)
        final_result['data'] = response['input']
        final_result['transaction_index'] = int(response['transactionIndex'], 0)
        final_result['height'] = long(response['blockNumber'], 0)
        final_result['blockhash'] = response['blockHash']
        return final_result

    def parse_transaction_receipt(self, response):
        final_result = {
            'txid': response['transactionHash'],
        }
        final_result['from_address'] = response['from']
        final_result['to_address'] = response['to']
        final_result['blockhash'] = response['blockHash']
        final_result['contract_address'] = response['contractAddress']
        final_result['transaction_status'] = response['status']
        final_result['height'] = long(response['blockNumber'], 0)
        final_result['fees_used'] = long(response['gasUsed'], 0)
        final_result['cumulative_fees_used'] = long(response['cumulativeGasUsed'], 0)
        return final_result

    def get_transaction_by_hash(self, hash_key):
        response = self._post('eth_getTransactionByHash', [hash_key])
        result = response['result']
        # convert to uniform format
        return self.parse_transaction_response(result)

    def get_transaction_receipt(self, hash_key):
        response = self._post('eth_getTransactionReceipt', [hash_key])
        result = response['result']
        return self.parse_transaction_receipt(result)

    def get_balance_by_address(self, address):
        response = self._post('eth_getBalance', [address, "latest"])
        result = str(long(response['result'], 0))
        return result

    def send_transaction(self, rawtx):
        response = self._post('eth_sendRawTransaction', [rawtx])
        result = response['result']
        return result

    def load_validator_lib(self):
        current_path = os.path.abspath(__file__)
        index = current_path.rfind('/')
        current_path = current_path[:index] + '/cliquesigner.so'
        validator_lib = cdll.LoadLibrary(current_path)
        return validator_lib

    def get_validator(self, validator_lib, block_info):
        blockJson = json.dumps(block_info)
        class GoString(Structure):
            _fields_ = [("p", c_char_p), ("n", c_longlong)]
        validator_lib.GetSignerByBlockJSON.argtypes = [GoString]
        validator_lib.GetSignerByBlockJSON.restype = GoString
        blockJsonGoString = GoString(blockJson, len(blockJson))
        ret = validator_lib.GetSignerByBlockJSON(blockJsonGoString)
        logger.debug('validator_result:%s' % ret.p)
        if len(ret.p) == 42:
            return ret.p
        else:
            return ''

if __name__ == '__main__':
    url = 'http://explorer.newtonproject.dev.diynova.com:8501'
    provider = Provider(url)
    # get block height
    print provider.get_block_height()
    address_str = "0xe33eb7666bba40eccca84cf7a8d623735fa566d5"
    balance = provider.get_balance_by_address(address_str)
    print "balance %s" % str(balance)
    # get block by height
    # print provider.get_block_height(1)
    # get transaction count 
    print provider.get_transaction_count_by_height(1)
    # get transaction by height and index
    # print provider.get_transaction_by_height_and_index(2, 0)
    # get block by hash
    # get transaction by hash
    # get utxos by address
    # get balance by address

from django.test import TestCase
from provider_newton import Provider
from utils import newchain_tools
import base58
from ctypes import *


class ProviderTestCase(TestCase):
    # def test_celery_data(self):
    #     url = 'http://explorer.newtonproject.dev.diynova.com:8501'
    #     provider = Provider(url)
    #     newton_addr = 'NEW132Ajd7xyyRfaLVCuRBQvvfXNoHrWVfGE4PvX'
    #     translation = newchain_tools.NewChainAddress()
    #     addr = translation.b58check_decode(newton_addr)
    #     balance = provider.get_balance_by_address(addr)
    #     print(balance)

    def test_recevie_data(self):
        # url = 'http://explorer.newtonproject.dev.diynova.com:8501'
        # provider = Provider(url)
        # response = provider._post('eth_getBlockByNumber', ['0x%x' % 88472, True])
        # result = response.get('result')
        # data = result['parentHash']
        # print(result)
        # print(data)
        so = cdll.LoadLibrary('./cliquesigner.so')
        so.GetSignerByBlockNumber.argtypes = [c_char_p, c_int64]
        addr = so.GetSignerByBlockNumber('https://rpc_address_here', 100)
        print(addr)

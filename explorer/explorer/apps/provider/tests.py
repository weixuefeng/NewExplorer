from django.test import TestCase
from provider_newton import Provider
from utils import newchain_tools
import base58
from ctypes import *
from config import server
from services import *
from provider import models as provider_models


class ProviderTestCase(TestCase):
    # def test_celery_data(self):
    #     url = 'http://explorer.newtonproject.dev.diynova.com:8501'
    #     provider = Provider(url)
    #     newton_addr = 'NEW132Ajd7xyyRfaLVCuRBQvvfXNoHrWVfGE4PvX'
    #     translation = newchain_tools.NewChainAddress()
    #     addr = translation.b58check_decode(newton_addr)
    #     balance = provider.get_balance_by_address(addr)
    #     print(balance)

    # def test_recevie_data(self):
    #     url = 'http://explorer.newtonproject.dev.diynova.com:8501'
    #     provider = Provider(url)
    #     response = provider._post('eth_getBlockByNumber', ['0x%x' % 88472, True])
    #     result = response.get('result')
    #     data = result['parentHash']
    #     print(result)
    #     print(data)

    # def test_recevie_validata(self):
    #     lib = cdll.LoadLibrary("/home/fivemeter/Desktop/newton-explorer/explorer/explorer/apps/provider/cliquesigner.so")
    #     class GoString(Structure):
    #         _fields_ = [("p", c_char_p), ("n", c_longlong)]

    #     lib.GetSignerByBlockNumber.argtypes = [GoString, c_longlong]
    #     lib.GetSignerByBlockNumber.restype = GoString

    #     urlstr = b"https://rpc1.newchain.newtonproject.org/"
    #     url = GoString(urlstr, len(urlstr))
    #     for i in range(2299703, 2299715):
    #         ret = lib.GetSignerByBlockNumber(url, i)
    #         print(i, ret.p)

    # def test_store_validator(self):
    #     url = 'http://explorer.newtonproject.dev.diynova.com:8501'
    #     provider = Provider(url)
    #     rpc_url = server.RPC_URL
    #     ret = provider.get_validate_node(rpc_url, 300)
    #     print(ret.p)

    def test_sync_validator_data(self):
        validator_address = "0xa0ADaEd410e3f70f582F4C66689Ac32b41F2f749"
        sync_validator_data(validator_address)
        instance = provider_models.Validator.objects.filter(address=validator_address)
        self.assertEqual(instance.count(), 1)




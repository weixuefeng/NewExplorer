from django.test import TestCase
from provider_newton import Provider
from utils import newchain_tools
import base58


class ProviderTestCase(TestCase):
    def test_celery_data(self):
        url = 'http://explorer.newtonproject.dev.diynova.com:8501'
        provider = Provider(url)
        newton_addr = 'NEW132Ajd7xyyRfaLVCuRBQvvfXNoHrWVfGE4PvX'
        translation = newchain_tools.NewChainAddress()
        addr = translation.b58check_decode(newton_addr)
        balance = provider.get_balance_by_address(addr)
        print(balance)
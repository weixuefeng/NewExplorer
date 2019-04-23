# -*- coding: utf-8 -*-
"""
Cryptography, address, transaction manipulation for newchain.
"""
__copyright__ = """ Copyright (c) 2018 Newton Foundation. All rights reserved."""
__version__ = '1.0'
__author__ = 'yanhang@diynova.com'


import base58
from django.conf import settings

class NewChainAddress(object):
    def __init__(self):
        self.chainID = settings.CHAIN_ID
        self.PREFIX = 'NEW'

    def address_encode(self, address_data):
        if address_data.startswith('0x'):
            address_data = address_data[2:]
        hex_chainID = hex(self.chainID)[2:]
        if len(hex_chainID) < 4:
            hex_chainID = '0' + hex_chainID
        num_sum = hex_chainID + address_data
        data = base58.b58encode_check(b'\0' + num_sum.decode('hex'))
        new_address = self.PREFIX + data
        return new_address


    def b58check_decode(self, new_address):
        """ Decoding function """
        new_address = base58.b58decode_check(bytes(new_address[3:]))
        address_data = '0x' + new_address.encode('hex')[6:]
        return address_data

    def is_valid_address(self, new_address):
        new_address = base58.b58decode_check(bytes(new_address[3:]))
        return int(new_address.encode('hex')[:6], 16) == self.chainID


if __name__ == "__main__":
    Adec = NewChainAddress()
    new_address = u'NEW132APq4ipFz774M9AsvdY9zkJweSKAsV2n4Mm'
    print(new_address.encode('utf-8'))
    # new_address = Adec.address_encode(bytes(address_data)
    decode_result = Adec.b58check_decode(bytes(new_address))
    print(decode_result)


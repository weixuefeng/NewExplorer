# -*- coding: utf-8 -*-
__author__ = 'yanhang@diynova.com'
__version__ = '$Rev$'
__doc__ = """  """

import base58

class NewChainAddress(object):
    def __init__(self):
        self.chainID = 16888
        self.PREFIX = 'NEW'

    def address_encode(self,address_data):
        hex_chainID = hex(self.chainID)[2:]
        num_sum = hex_chainID + address_data
        data = base58.b58encode_check(b'\0' + num_sum.decode('hex'))
        new_address = self.PREFIX + data
        print('Encode result', new_address)
        return new_address


    def b58check_decode(self,new_address):
        """ Decoding function """
        new_address = base58.b58decode_check(new_address[3:])
        address_data = new_address.encode('hex')[6:]
        print('Decode result',address_data)
        return address_data

if __name__ == "__main__":
    Adec = NewChainAddress()
    address_data = '96ec0f4a194e653f1ed8aedd38183be564700e17'
    print('initial input',address_data)
    new_address = Adec.address_encode(address_data)
    decode_result = Adec.b58check_decode(new_address)


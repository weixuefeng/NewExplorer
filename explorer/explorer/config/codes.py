# -*- coding: utf-8 -*-
__author__ = 'xiawu@xiawu.org'
__version__ = '$Rev$'
__doc__ = """  """

from enum import Enum


class ErrorCode(Enum):
    FAIL = 0
    SUCCESS = 1
    UNAUTH = 2
    SIGN_ERROR = 3
    INVALID_PARAMS = 4
    MAINTAIN = 5
    UPGRADE = 6
    # common
    INVALID_AUTH = 100
    WRONG_PASSWORD = 101
    WRONG_CELLPHONE = 102
    INFORMAT_PASSWORD_CELLPHONE = 103
    BLOCK_USER = 104
    UNIT_USER_NOT_EXIST = 105
    WRONG_EMAIL = 106

class Language(Enum):
    CHINESE = 1
    ENGLISH = 2

class BlockChainType(Enum):
    BITCOIN = 1
    ETHEREUM = 2
    NEWTON = 3

class ValueType(Enum):
    RECEIVE = 1
    SEND = 2

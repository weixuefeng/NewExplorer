# -*- coding: utf-8 -*-
__author__ = 'xiawu@xiawu.org'
__version__ = '$Rev$'
__doc__ = """  """


from django.conf import settings
from config import codes


def settings_variable(context):
    return {
        'codes': codes,
        'settings': settings,
    }

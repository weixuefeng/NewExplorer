# -*- coding: utf-8 -*-
"""
Django settings for education project.

"""
from config import codes

# import common settings 
from config.common_settings import *
from config.settings_label import *

APPEND_SLASH = True

LOGGING_API_REQUEST = True

STATIC_DEFAULT_VERSION = 42
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    "django.core.context_processors.request",
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.csrf',
    'context_processors.settings_variable',
)

# misc
PAGE_SIZE = 50

# coin
UNIT_TO_SATOSHI = 100000000

# cache
CACHE_KEY_NEWBLOCK = 'newblock'

# -*- coding: utf-8 -*-
"""
Django settings for education project.

"""
from config import codes

# import common settings 
from config.common_settings import *
from config.settings_label import *

SITE_ID = '1'
APPEND_SLASH = True

LOGGING_API_REQUEST = True

STATIC_DEFAULT_VERSION = 40
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


SESSION_COOKIE_AGE = 3600 * 24 * 365 * 10
SESSION_COOKIE_DOMAIN = '.newtonproject.org'
SESSION_SAVE_EVERY_REQUEST = True
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
CART_CACHE_TIME = 3600 * 24 * 30

# website meta
BASE_URL = 'http://explorer.newtonproject.org'
BASE_NAME = 'explorer'

# misc
PAGE_SIZE = 50

# coin
UNIT_TO_SATOSHI = 100000000

# cache
CACHE_KEY_NEWBLOCK = 'newblock'

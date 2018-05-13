# -*- coding: utf-8 -*-
__author__ = 'xiawu@xiawu.org'
__version__ = '$Rev$'
__doc__ = """  """

from enum import Enum
from config import codes
from server import *

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'zh-CN'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/
STATIC_URL = 'http://static.lubangame.com/static/'
STATIC_ROOT = 'lubangame/static'

# LOGGING
import platform
system_string = platform.system()
if system_string == 'Linux':
    syslog_path = '/dev/log'
elif system_string == 'Darwin':
    syslog_path = '/var/run/syslog'
else:
    raise Exception('Upsupport platform!')

from logging.handlers import SysLogHandler
LOGGING_LEVEL = 'INFO'
LOGGING_LEVEL_SENTRY = 'ERROR'
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s][%(msecs)03d] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'syslog': {
            'level': LOGGING_LEVEL,
            'class': 'logging.handlers.SysLogHandler',
            'facility': SysLogHandler.LOG_LOCAL2,
            'formatter': 'verbose',
            'address': syslog_path,
        },
        'sentry': {
            'level': LOGGING_LEVEL_SENTRY,
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
            'tags': {'custom-tag': 'x'},
        },
    },
    'loggers': {
        '': {
            'handlers': ['syslog', ],
            'level': LOGGING_LEVEL,
        },
        'django': {
            'handlers': ['syslog', ],
            'propagate': True,
            'level': LOGGING_LEVEL,
        },
        'celery.task': {
            'handlers': ['syslog', ],
            'propagate': True,
            'level': LOGGING_LEVEL,
        }
    }
}

SESSION_COOKIE_AGE = 3600 * 24 * 365 * 10
SESSION_COOKIE_DOMAIN = '.newtonproject.org'
SESSION_COOKIE_NAME = 'esid'
SESSION_SAVE_EVERY_REQUEST = True
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "session"
CART_CACHE_TIME = 3600 * 24 * 30
ACCESS_TOKEN_CACHE_TIME = 0

# Proxy settings
USE_X_FORWARDED_HOST = True

# File server storage
MEDIA_ROOT = '/data/newton-storage/filestorage'
MEDIA_URL = 'http://explorer.newtonproject.org/filestorage/'

# website meta
BASE_URL = 'http://explorer.newtonproject.org'
BASE_NAME = 'explorer'

# User Default Preferred Language Code
USER_DEFAULT_LANGUAGE_CODE = 'zh-CN'

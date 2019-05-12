# -*- coding: utf-8 -*-
__author__ = 'xiawu@zeuux.org'
__version__ = '$Rev$'
__doc__ = """  """

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/
STATIC_URL = 'http://explorer.test.newtonproject.org/static/'
STATIC_ROOT = 'explorer/static'

# website meta
SITE_ID = '1'
BASE_NAME = 'explorer'

# domain settings
DEBUG = True
TEMPLATE_DEBUG = False
THUMBNAIL_DEBUG = False
DOMAIN = 'explorer.test.newtonproject.org'
BASE_URL = 'http://explorer.test.newtonproject.org'
MEDIA_URL = 'http://explorer.test.newtonproject.org/filestorage/'
MEDIA_ROOT = './'

#session settings
SESSION_COOKIE_AGE = 3600 * 24 * 365 * 10
SESSION_COOKIE_DOMAIN = '.test.newtonproject.org'
SESSION_SAVE_EVERY_REQUEST = True
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_NAME = 'nesid'

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
LOGGING_LEVEL = 'DEBUG'
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
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', ],
            'level': LOGGING_LEVEL,
        },
        'django': {
            'handlers': ['console', ],
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

# Cache
DEFAULT_CACHE_DB = 1
WORKER_CACHE_DB = 8
REDIS_CACHE_DB = DEFAULT_CACHE_DB
REDIS_CACHE_PASSWORD = ''
REDIS_CACHE_HOST = '127.0.0.1'
REDIS_CACHE_PORT = 6379
REDIS_CACHE_URL = 'redis://%s:%s' % (REDIS_CACHE_HOST, REDIS_CACHE_PORT)
REDIS_WORKER_URL = 'redis://127.0.0.1:6379'
REDIS_LOCAL_GAME_URL = 'redis://127.0.0.1:6379'

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "%s/%s" % (REDIS_CACHE_URL, DEFAULT_CACHE_DB),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'explorer',
        'USER': 'root',
        'PASSWORD': ''
    }
}

# Following is project settings
MONGODB_HOST = 'localhost'
BLOCK_CHAIN_DB_NAME = 'blockchain'

# full node list
FULL_NODES = {
    'new': {
        'node_type': 3,
        'rest_url': 'https://rpc1.newchain.newtonproject.org',
        'ws_url': 'https://rpc1.newchain.newtonproject.org',
    }
}
DEFAULT_MONITOR_PORT = 8090

CURRENT_NET = 'TestNet'

CHAIN_ID = 1007

import djcelery
djcelery.setup_loader()
BROKER_URL = '%s/%s' % (REDIS_WORKER_URL, WORKER_CACHE_DB)
CELERY_RESULT_BACKEND = '%s/%s' % (REDIS_WORKER_URL, WORKER_CACHE_DB)
CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']
CELERYD_HIJACK_ROOT_LOGGER = False
CELERY_IMPORTS = ('tasks.task_report',)

from datetime import timedelta
CELERYBEAT_SCHEDULE = {
    'sync-blockchain-data': {
        'task': 'tasks.task_report.execute_sync_blockchain',
        'schedule': timedelta(seconds=3),        
    },
}

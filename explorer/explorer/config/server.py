# -*- coding: utf-8 -*-
__author__ = 'xiawu@xiawu.org'
__version__ = '$Rev$'
__doc__ = """  """

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

MONGODB_HOST = 'localhost'
BLOCK_CHAIN_DB_NAME = 'blockchain'

# full node list
FULL_NODES = {
    'new': {
        'node_type': 3,
        'rest_url': 'http://47.91.208.241:8801',
        'ws_url': 'http://47.91.208.241:8801',
    }
}
DEFAULT_MONITOR_PORT = 8090

# celery settings
import djcelery
djcelery.setup_loader()
BROKER_URL = '%s/%s' % (REDIS_WORKER_URL, WORKER_CACHE_DB)
CELERY_RESULT_BACKEND = '%s/%s' % (REDIS_WORKER_URL, WORKER_CACHE_DB)
CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']
EMAIL_BACKEND = 'djcelery_email.backends.CeleryEmailBackend'
CELERYD_HIJACK_ROOT_LOGGER = False
CELERY_EMAIL_TASK_CONFIG = {
    'queue' : 'email',
    'rate_limit' : '50/m',
}

CELERY_IMPORTS = ('tasks.task_report', )

from celery.schedules import crontab
from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    'report-1-minites': {
        'task': 'tasks.task_report.execute_sync_blockchain',
        'schedule': timedelta(seconds=10),        
    },
}

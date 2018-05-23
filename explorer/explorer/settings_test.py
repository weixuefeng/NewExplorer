from settings import *

DEBUG = True
TEMPLATE_DEBUG = True
THUMBNAIL_DEBUG = True
STATIC_URL = 'http://localhost:8000/static/'
DOMAIN = 'test.lubangame.com'
SESSION_COOKIE_DOMAIN = None
MEDIA_URL = 'http://localhost:8000/filestorage/'
MEDIA_ROOT = BASE_DIR

# LOGGING
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/tmp/newton.log',
            'formatter': 'verbose'
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        '': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
        },
        'django': {
            'handlers': ['file', 'console'],
            'propagate': True,
            'level': 'DEBUG',
        },
    }
}

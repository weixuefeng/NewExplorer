# -*- coding: utf-8 -*-
"""
Django settings for lubangame project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import sys

import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_ROOT = os.path.join(BASE_DIR, "explorer")

# Add the individual app package path
sys.path.insert(0, os.path.join(PROJECT_ROOT, "apps"))
sys.path.insert(0, PROJECT_ROOT)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'e*qqt+xfyi!t^fq%znwtnqjk0^^$pzae6&u1)+*l8^s%^-yi_c'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

TEMPLATE_DEBUG = False

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djcelery',
    'email_log',
    # main entry
    'explorer',
    # apps
    'base',
    'welcome',
    'provider',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
     #'django.middleware.locale.LocaleMiddleware',
    'middlewares.locale_middleware.LocaleFromPostMiddleware',
    'middlewares.timezone_middleware.TimezoneFromPostMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'explorer.urls'

WSGI_APPLICATION = 'explorer.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'zh-CN'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


LOCALE_PATHS = (
    os.path.join(BASE_DIR, "locale"),
)

# Template root directory
TEMPLATE_DIRS = [os.path.join(PROJECT_ROOT, "templates")]

try:
    from settings_local import *
except Exception, inst:
    print inst

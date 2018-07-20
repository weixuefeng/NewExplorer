# -*- coding: utf-8 -*-
from django.shortcuts import render

__author__ = 'xiawu@zeuux.org'
__version__ = '$Rev$'
__doc__ = """  """

import json
import random

from django.conf import settings
from django.http import HttpResponse
from django.core.cache import cache

def home(request):
    return render(request, 'ui/public/index-template.html')
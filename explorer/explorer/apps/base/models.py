# -*- coding: utf-8 -*-
from django.db import models
from config import codes

__author__ = 'xiawu@xiawu.org'
__version__ = '$Rev$'
__doc__ = """  The definition of global abstract models """

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

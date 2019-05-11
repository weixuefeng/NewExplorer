"""
Locale Middlwares Implementation includeing POST parameter, HTTP Header, etc.

"""

__copyright__ = """ Copyright (c) 2018 Newton Foundation. All rights reserved."""
__version__ = '1.0'
__author__ = 'liuda@lubangame.com'


from django.utils import translation
from django.middleware import locale
from django.conf import settings


class LocaleFromPostMiddleware(locale.LocaleMiddleware):
    """
    LocaleFromPostMiddleware: Set the current language code by language filed in POST parameters
    """
    def __get_user_language(self, request):
        try:
            language = request.COOKIES.get('language')
            if not language:
                language = request.META.get('HTTP_ACCEPT_LANGUAGE')
            if not language:
                language = request.POST.get("language", None)
            if not language:
                return settings.LANGUAGE_CODE
            if language.find('zh') >= 0:
                return 'zh_CN'
            return 'en'
        except Exception, inst:
            logger.exception('fail to get user language:%s' % str(inst))
            return ''

    def process_request(self, request):
        # check the langage in cookie
        language = self.__get_user_language(request)
        if not language:
            language = settings.LANGUAGE_CODE
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()

    def process_response(self, request, response):
        response['Access-Control-Allow-Origin'] = '*'
        return response

"""
Get and set timezone information from request

"""

__copyright__ = """ Copyright (c) 2018 Newton Foundation. All rights reserved."""
__version__ = '1.0'
__author__ = 'liuda@lubangame.com'


class TimezoneFromPostMiddleware(object):
    """
    Get timezone informatino from POST.timezone
    """
    def process_request(self, request):
        try:
            timezone = request.POST.get("timezone", None)
            if timezone:
                if timezone.startswith("GMT"):
                    timezone = timezone[3:]
                timezone = int(timezone)
                if timezone in range(-12, 13):
                    request.TIMEZONE = timezone
            else:
                request.TIMEZONE = 8
        except:
            request.TIMEZONE = 8

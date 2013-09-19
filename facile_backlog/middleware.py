from __future__ import unicode_literals

from django.conf import settings
from django.utils import translation, timezone
from django.utils.cache import patch_vary_headers


class LocaleMiddleware(object):
    """
    This is a very simple middleware that parses a request
    and decides what translation object to install in the current
    thread context depending on the user's language. This allows pages
    to be dynamically translated to the language the user desires
    (if the language is available, of course).
    """

    def get_language_for_user(self, request):
        lang = getattr(request.user, 'lang', None)
        if lang:
            return lang
        return translation.get_language_from_request(request)

    def process_request(self, request):
        translation.activate(self.get_language_for_user(request))
        request.LANGUAGE_CODE = translation.get_language()

    def process_response(self, request, response):
        patch_vary_headers(response, ("Accept-Language",))
        response["Content-Language"] = translation.get_language()
        translation.deactivate()
        return response


class TimezoneMiddleware(object):
    """
    This middleware sets the timezone used to display dates in
    templates to the user's timezone.
    """

    def process_request(self, request):
        time_zone = getattr(request.user, "account", None)
        tz = settings.TIME_ZONE if not time_zone else time_zone
        timezone.activate(tz)

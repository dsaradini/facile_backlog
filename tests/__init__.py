import os
import random
import re
import string
import json

from rest_framework.authtoken.models import Token

from django.test.client import FakePayload, urlparse, force_str
from django.test import TestCase, Client


TEST_DATA = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')

with open(os.path.join(TEST_DATA, "lorem.txt"), "r") as f:
    # striping lowering and all those stuff may be done in the original
    # lorem.txt file
    data = f.read().decode('utf-8')
    data = re.sub(r"""[\.,\n\r'"]""", "", data)
    LOREM_WORDS = map(lambda w: w.lower(), data.split(" "))


def rand_lorem_word():
    """
    Return a random word
    """
    return random.choice(LOREM_WORDS)


def rand_lorem_phrase(min=1, max=100):
    """
    Return a random phrase containing 'n' words.
    where 'n' is contained between 'min' and 'max'
    """
    max = random.randrange(min - 1, max)
    phrase = rand_lorem_word().capitalize()
    for i in range(max):
        x = random.randint(0, 20)
        if x == 1:
            phrase = u"{0}. {1}".format(phrase, rand_lorem_word().capitalize())
        elif x < 4:
            phrase = u"{0}, {1}".format(phrase, rand_lorem_word())
        else:
            phrase = u"{0} {1}".format(phrase, rand_lorem_word())
    return phrase[:-1] + "."


def rand_color():
    """
    Return a random color string between "#000000" and "#ffffff"
    """
    return "#{0:0>6x}".format(random.randint(0, 16777215))


def rand_ascii(min_val, max_val):
    return "".join([random.choice(string.ascii_letters)
                    for i in range(random.randint(min_val, max_val))])


def rand_domain():
    return "{0}.{1}".format(rand_ascii(4, 20), rand_ascii(2, 4))


def rand_email():
    return "{0}@{1}".format(rand_ascii(4, 50), rand_domain())


def line_starting(text, start):
    for l in text.split("\n"):
        if l.find(start) == 0:
            return l
    return None


def user_token_auth(user):
    token, create = Token.objects.get_or_create(user=user)
    return api_token_auth(token)


class ApiClient(Client):
    def request(self, **request):
        user = request.pop("user", None)
        if user:
            request.update(user_token_auth(user))
        response = super(ApiClient, self).request(**request)
        if response.content and \
           response.get("Content-Type", "").find('application/json') != -1:
            response.json = json.loads(response.content)
        else:
            response.json = None
        status = request.get("status", 200)
        check_status = not response.status_code in (301, 302, 303, 307)
        if check_status and status != response.status_code:
            raise ValueError("Response return {0} not {1}".format(
                response.status_code, status))
        return response

    def patch(self, path, data={}, content_type='application/json',
              follow=False, **extra):
        """
        Requests a response from the server using PATH.
        """
        post_data = self._encode_data(data, content_type)
        parsed = urlparse(path)
        r = {
            'CONTENT_LENGTH': len(post_data),
            'CONTENT_TYPE':   content_type,
            'PATH_INFO':      self._get_path(parsed),
            'QUERY_STRING':   force_str(parsed[4]),
            'REQUEST_METHOD': str('PATCH'),
            'wsgi.input':     FakePayload(post_data),
        }
        r.update(extra)
        response = self.request(**r)
        if follow:
            response = self._handle_redirects(response, **extra)
        return response


class JsonTestCase(TestCase):
    client_class = ApiClient

    def assertJsonKeyEqual(self, response, key, reference, status_code=200):  # noqa
        self.assertEqual(response.status_code, status_code)
        json1 = response.json
        if key not in json1:
            raise AssertionError("Json content has no key '{0}'".format(key))
        if json1[key] != reference:
            raise AssertionError(
                "json content ['{0}]' not equal"
                " '{1}' != '{2}'".format(key, json1[key], reference)
            )


def api_token_auth(token):
    return {'HTTP_AUTHORIZATION': 'Token {0}'.format(token)}

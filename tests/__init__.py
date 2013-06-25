import os
import random
import re
import string
import json

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


class ApiClient(Client):
    def request(self, **request):
        response = super(ApiClient, self).request(**request)
        if response.get("Content-Type", "").find('application/json') != -1:
            response.json = json.loads(response.content)
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

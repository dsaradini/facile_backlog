import hashlib
import string

from django.template import Library

register = Library()


@register.filter(is_safe=False)
def hashcolor(obj):
    return create_hash_color(obj)


def create_hash_color(text):
    md5 = hashlib.md5(filter(lambda x: x in string.printable, text))
    return "#{0}".format(md5.hexdigest()[:6])

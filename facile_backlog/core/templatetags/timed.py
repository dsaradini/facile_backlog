import datetime

from django.template import Library

from timedelta import helpers

register = Library()


@register.filter(is_safe=False)
def timedelta(obj):
    return helpers.nice_repr(obj)


@register.filter
def total(grouper_list, attrib):
    total = datetime.timedelta()
    for d in grouper_list:
        to_add = getattr(d, attrib)
        if isinstance(to_add, datetime.timedelta):
            total += to_add
    return total
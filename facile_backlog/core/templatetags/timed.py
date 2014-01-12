from django.template import Library
from ..workload import to_string

register = Library()


@register.filter(is_safe=False)
def timedelta(obj, by_day=0):
    if not obj:
        return "N/A"
    return to_string(obj, by_day)


@register.filter
def totaltime(grouper_list, attrib):
    total = 0.0
    for d in grouper_list:
        to_add = getattr(d, attrib)
        total += to_add
    return total


@register.filter(is_safe=False)
def timedsign(obj):
    if obj < 0:
        return '-'
    elif obj > 0:
        return "+"
    return ""



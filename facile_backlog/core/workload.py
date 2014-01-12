import re

from django.utils import six


def to_string(total_sec, by_day=0, display="long", sep=", "):
    if not total_sec:
        return ""
    result = []

    if by_day:
        days = total_sec / by_day
        seconds = total_sec % by_day
    else:
        days = 0
        seconds = total_sec
    hours = seconds / 3600
    seconds = seconds % 3600
    minutes = seconds / 60
    seconds = seconds % 60

    if display == 'minimal':
        words = ["d", "h", "m", "s"]
    elif display == 'short':
        words = [" days", " hrs", " min", " sec"]
    else:
        words = [" days", " hours", " minutes", " seconds"]

    values = [days, hours, minutes, seconds]

    for i in range(len(values)):
        if values[i]:
            if values[i] == 1 and len(words[i]) > 1:
                result.append("%i%s" % (values[i], words[i].rstrip('s')))
            else:
                result.append("%i%s" % (values[i], words[i]))

    return sep.join(result).strip()


def parse(string, by_day=0):
    """
    Parse a string into a timedelta object.
    """
    if string == "":
        raise TypeError("'%s' is not a valid time" % string)
    # This is the format we get from sometimes Postgres, sqlite,
    # and from serialization
    d = re.match(
        r'^((?P<days>[-+]?\d+) days?,? )?(?P<sign>[-+]?)(?P<hours>\d+):'
        r'(?P<minutes>\d+)(:(?P<seconds>\d+(\.\d+)?))?$',
        six.text_type(string)
    )
    if d:
        d = d.groupdict(0)
        if d['sign'] == '-':
            for k in 'hours', 'minutes', 'seconds':
                d[k] = '-' + d[k]
        d.pop('sign', None)
    else:
        # This is the more flexible format
        d = re.match(
            r'^((?P<weeks>-?((\d*\.\d+)|\d+))\W*w((ee)?(k(s)?)?)(,)?\W*)?'
            r'((?P<days>-?((\d*\.\d+)|\d+))\W*d(ay(s)?)?(,)?\W*)?'
            r'((?P<hours>-?((\d*\.\d+)|\d+))\W*h(ou)?(r(s)?)?(,)?\W*)?'
            r'((?P<minutes>-?((\d*\.\d+)|\d+))\W*m(in(ute)?(s)?)?(,)?\W*)?'
            r'((?P<seconds>-?((\d*\.\d+)|\d+))\W*s(ec(ond)?(s)?)?)?\W*$',
            six.text_type(string)
        )
        if not d:
            raise TypeError("'%s' is not a valid time interval" % string)
        d = d.groupdict(0)

    total = 0.0
    total += float(d['seconds'])
    total += (float(d['minutes']) * 60)
    total += (float(d['hours']) * 3600)
    if by_day:
        total += (float(d['days']) * by_day)
    return total

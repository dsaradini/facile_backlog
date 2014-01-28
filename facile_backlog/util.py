import hashlib

from django.conf import settings


def gravatar_url(email, size=32):
    return "https://www.gravatar.com/avatar/{0}?s={1}".format(
        hashlib.md5(email).hexdigest(),
        size,
    )


def setup_bootstrap_fields(form, fields=None):
    for name in form.fields:
        if fields and name not in fields:
            continue
        field = form.fields[name]
        clazz = field.widget.attrs.get("class", "")
        clazz = "{0} {1}".format(clazz, "form-control input-large")
        field.widget.attrs["class"] = clazz


def get_websocket_url(request):
    websocket_url = settings.WEBSOCKET_URL
    host = request.META.get("HTTP_HOST", "localhost")
    try:
        index = host.index(":")
        if index:
            host = host[:index]
    except Exception:
        pass
    return websocket_url.format(**{
        'host': host
    })

import hashlib


def gravatar_url(email, size=32):
    return "https://www.gravatar.com/avatar/{0}?s={1}".format(
        hashlib.md5(email).hexdigest(),
        size,
    )

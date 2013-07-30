from settings import *  # noqa

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

EASYBACKLOG_TOKEN = "test-easybacklog-token"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'backlog.sqlite',
    }
}

API_THROTTLE = None

# Don't bother with PBKDF2 in tests. This saves a **lot** of time.
PASSWORD_HASHERS = [
    'tests.hashers.NotHashingHasher',
]

LOGGING['loggers']['facile_backlog']['level'] = 'ERROR'
LOGGING['loggers']['raven']['level'] = 'ERROR'

from settings import *  # noqa

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

EASYBACKLOG_TOKEN = "test-easybacklog-token"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'backlog.sqlite',
    }
}

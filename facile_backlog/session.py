from django.contrib.sessions.backends.cache import SessionStore as SessionBase


class SessionStore(SessionBase):
    @property
    def cache_key(self):
        return 'backlogman.websession:' + self._get_or_create_session_key()

import json

import tornado.web
import logging
import tornado.websocket

import django.conf
import django.contrib.auth
import django.core.handlers.wsgi
import django.db
import django.utils.importlib

import pprint

clients = []


def write_to_clients(data):
    for c in clients:
        if c.ws_connection:
            c.write_message(data)


class SocketHandler(tornado.websocket.WebSocketHandler):

    def open(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        self.user = self.get_current_user()
        if not self.user:
            self.close()
            return
            # raise Exception("Not logged in")
        logger.debug("opening : {0}".format(self.user))
        if self not in clients:
            clients.append(self)
        logger.debug("Client count: {0}".format(len(clients)))

    def on_closed(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        logger.debug("closing")
        if self in clients:
            clients.remove(self)

    def on_message(self, message):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        logger.debug("message received")
        data = json.loads(message)
        data['username'] = self.user.full_name
        write_to_clients(data)

    def get_django_session(self):
        if not hasattr(self, '_session'):
            engine = django.utils.importlib.import_module(
                django.conf.settings.SESSION_ENGINE)
            session_key = self.get_cookie(
                django.conf.settings.SESSION_COOKIE_NAME)
            self._session = engine.SessionStore(session_key)
        return self._session

    def get_current_user(self):
        # get_user needs a django request object, but only looks at the session
        class Dummy(object):
            pass
        django_request = Dummy()
        django_request.session = self.get_django_session()
        user = django.contrib.auth.get_user(django_request)
        if user.is_authenticated():
            return user
        else:
            return None
import json
import threading
from collections import defaultdict

import tornado.web
import logging
import tornado.websocket

from django.conf import settings
from tornado.ioloop import IOLoop
import django.contrib.auth
import django.core.handlers.wsgi
import django.db
import django.utils.importlib

import redis

CLIENTS = defaultdict(set)

NOTIFICATION_CHANNEL = "realtime_notif"
REDIS_DB = 2

logger = logging.getLogger(__name__)


def redis_listener():
    host, _, port = settings.REDIS_URL.partition(":")
    r = redis.Redis(host=host, port=int(port), db=REDIS_DB)
    ps = r.pubsub()
    ps.subscribe(NOTIFICATION_CHANNEL)
    io_loop = IOLoop.instance()
    logger.debug("Redis listener started on channel {0}".format(
        NOTIFICATION_CHANNEL))

    for message in ps.listen():
        logger.debug("Message {0}".format(message))
        if message['type'] == 'message':
            try:
                data = json.loads(message['data'])
                key = data['key']
                message = data['data']
                io_loop.add_callback(write_to_clients,src_client=key,
                                     data=message)
            except Exception:
                logger.warn(
                    "Received wrong message from redis {0}".format(message))


def start_listener():
    threading.Thread(target=redis_listener).start()


def append_client(client):
    key = client.client_key
    CLIENTS[key].add(client)


def remove_client(client):
    key = client.client_key
    CLIENTS[key].discard(client)


def write_to_clients(src_client, data, self_message=True):
    logger.debug("Write to client {0} -> {1}".format(src_client, data))
    if isinstance(src_client, SocketHandler):
        key = src_client.client_key
    else:
        key = src_client
    for c in CLIENTS[key]:
        if c.ws_connection and c != src_client:
            c.write_message(data)


class SocketHandler(tornado.websocket.WebSocketHandler):

    def open(self, obj_type,  obj_id):
        self.user = self.get_current_user()
        self.obj_type = obj_type
        self.obj_id = obj_id
        self.client_key = "{0}:{1}".format(self.obj_type, self.obj_id)

        if not self.user:
            self.send_error(401)
            self.close()
            return
            # raise Exception("Not logged in")
        logger.debug("opening : {0}".format(self.user))
        append_client(self)

    def on_closed(self):
        logger.debug("closing")
        remove_client(self)

    def on_message(self, message):
        logger.debug("message received")
        data = json.loads(message)
        data['username'] = self.user.full_name
        write_to_clients(self, data)

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
             # try basic auth
            if not self.request.headers.has_key('Authorization'):
                return None
            kind, data = self.request.headers['Authorization'].split(' ')
            if kind != 'Basic':
                return None
            (username, _, password) = data.decode('base64').partition(':')
            user = django.contrib.auth.authenticate(username=username,
                                                    password=password)
            if user is not None and user.is_authenticated():
                return user
            return None
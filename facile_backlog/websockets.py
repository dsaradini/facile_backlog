import json
import logging
import datetime

from collections import defaultdict

from tornado.gen import coroutine, Task
from tornado.ioloop import IOLoop
from tornado.websocket import WebSocketHandler

from django.conf import settings
from django.contrib import auth
from django.utils import importlib

import tornadoredis

CLIENTS = defaultdict(set)

REDIS_RETRY_CONNECT = 5
WEBSOCKET_GARBAGE_CHECK = 20

NOTIFICATION_CHANNEL = "realtime_notif"
REDIS_DB = 2

logger = logging.getLogger(__name__)

client = None


def on_redis_message(message):
    if message.kind == 'message':
        try:
            io_loop = IOLoop.instance()
            data = json.loads(message.body)
            key = data['key']
            message = data['data']
            io_loop.add_callback(write_to_clients, src_client=key,
                                 data=message)
        except Exception:
            logger.warn(
                "Received wrong message from redis {0}".format(message))
    elif message.kind == 'disconnect':
        logger.info("Disconected from redis subscriber")
        listen()
    elif message.kind == 'subscribe':
        pass
    else:
        logger.debug("Received unknown message {0}".format(message))


@coroutine
def listen():
    global client
    host, _, port = settings.REDIS_URL.partition(":")
    client = tornadoredis.Client(host=host, port=int(port),
                                 selected_db=REDIS_DB)
    try:
        client.connect()
        yield Task(client.subscribe, NOTIFICATION_CHANNEL)
        client.listen(on_redis_message)
    except tornadoredis.ConnectionError as ex:
        logger.info(
            "redis connection error {0}, retrying to connect ...".format(ex))
        IOLoop.instance().add_timeout(datetime.timedelta(
            seconds=REDIS_RETRY_CONNECT
        ), listen)


@coroutine
def garbager():
    try:
        for k, c_list in CLIENTS.items():
            new_list = set([c for c in c_list if c.ws_connection is not None])
            CLIENTS[k] = new_list
            for c in c_list - new_list:
                logger.info(u"Disconnected {0}".format(c))
                _client_removed(c)
    finally:
        IOLoop.instance().add_timeout(datetime.timedelta(
            seconds=WEBSOCKET_GARBAGE_CHECK
        ), garbager)


def start_listener():
    listen()
    garbager()


def append_client(client):
    key = client.client_key
    CLIENTS[key].add(client)
    write_to_clients(client, json.dumps({
        'type': "user_join",
        'user': client.user.email,
        'users': [c.user.email for c in CLIENTS[key] if c.user]
    }))


def remove_client(client):
    key = client.client_key
    CLIENTS[key].discard(client)
    _client_removed(client)


def _client_removed(client):
    key = client.client_key
    write_to_clients(client, json.dumps({
        'type': "user_leave",
        'user': client.user.email,
        'users': [c.user.email for c in CLIENTS[key] if c.user]
    }))


def write_to_clients(src_client, data, self_notify=True):
    logger.debug("Write to client {0} -> {1}".format(src_client, data))
    if isinstance(src_client, SocketHandler):
        key = src_client.client_key
    else:
        key = src_client
    for c in CLIENTS[key]:
        if c.ws_connection:
            if self_notify or c != src_client:
                c.write_message(data)


class SocketHandler(WebSocketHandler):

    def __init__(self, *args, **kwargs):
        self._test_user = kwargs.pop("test_user", None)
        super(SocketHandler, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return u"WebSocket user[{0}] - Origin[{1}]".format(
            getattr(self, 'user', "anonymous"),
            self.request.headers.get("Origin", "unknown")
        )

    def open(self, obj_type,  obj_id):
        self.user = self.get_current_user()
        self.obj_type = obj_type
        self.obj_id = obj_id
        self.client_key = "{0}:{1}".format(self.obj_type, self.obj_id)

        if not self.user:
            self.close()
            return
            # raise Exception("Not logged in")
        logger.info(u"Opening {0}".format(self))
        append_client(self)

    def on_closed(self):
        logger.debug("closing")
        remove_client(self)

    def on_message(self, message):
        data = json.loads(message)
        data['username'] = self.user.full_name if self.user else "anonymous"
        write_to_clients(self, data)

    def get_django_session(self):
        if not hasattr(self, '_session'):
            engine = importlib.import_module(
                settings.SESSION_ENGINE)
            session_key = self.get_cookie(
                settings.SESSION_COOKIE_NAME)
            self._session = engine.SessionStore(session_key)
        return self._session

    def get_current_user(self):
        if self._test_user:
            return self._test_user

        # get_user needs a django request object, but only looks at the session
        class Dummy(object):
            pass
        django_request = Dummy()
        django_request.session = self.get_django_session()
        user = auth.get_user(django_request)
        if user.is_authenticated():
            return user
        else:
             # try api token auth
            return None

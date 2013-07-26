import datetime
import json

from functools import partial

from tornado.testing import AsyncHTTPTestCase, gen_test
from tornado.web import Application
from tornado.ioloop import IOLoop

from facile_backlog.websockets import SocketHandler, start_listener

from facile_backlog.api.notify import notify_changes

import websocket

from factories import UserFactory


class TestWebSockets(AsyncHTTPTestCase):
    def get_protocol(self):
        return "ws"

    def get_app(self):
        return Application([
            (r'/ws/(?P<obj_type>[\w]+)/(?P<obj_id>[\d]+)/$', SocketHandler,
             {"test_user": self._test_user}),
        ], debug=False)

    def get_new_ioloop(self):
        return IOLoop.instance()

    def setUp(self):
        self._test_user = UserFactory.create()
        super(TestWebSockets, self).setUp()

    @gen_test
    def test_web_socket(self):
        _self = self

        class WSClient(websocket.WebSocket):
            def on_open(self):
                self.write_message(json.dumps({
                    'type': 'test-message',
                    'data': 'hello',
                }))

            def on_message(self, data):
                mess = json.loads(data)
                t = mess['type']
                if t == 'test-end':
                    _self.io_loop.add_callback(_self.stop)
                elif t == 'user_join':
                    _self.assertEqual(mess['user'], _self._test_user.email)
                    _self.assertEqual(len(mess['users']), 1)
                elif t == 'test-message':
                    _self.assertEqual(mess['data'], "hello")
                else:
                    _self.fail("Unknown message {0}".format(mess))

        start_listener()
        self.io_loop.add_callback(
            partial(WSClient, self.get_url('/ws/projects/1/'), self.io_loop))

        def action():
            notify_changes("projects", 1, {
                'type': 'test-end'
            })

        self.io_loop.add_timeout(datetime.timedelta(seconds=1), action)
        self.wait()

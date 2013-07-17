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
                    'echo': 'test-message'
                }))

            def on_message(self, data):
                mess = json.loads(data)
                _self.assertEquals(mess['echo'], 'test-end')
                _self.io_loop.add_callback(_self.stop)

        start_listener()
        self.io_loop.add_callback(
            partial(WSClient, self.get_url('/ws/Project/1/'), self.io_loop))

        def action():
            notify_changes("Project", 1, {
                'echo': 'test-end'
            })

        self.io_loop.add_timeout(datetime.timedelta(seconds=1), action)
        self.wait()

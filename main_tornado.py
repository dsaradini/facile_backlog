import logging
import logging.config

import tornado.options
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import options, define
from tornado.web import Application

from django.conf import settings

from facile_backlog.websockets import (SocketHandler, start_listener)

logging.config.dictConfig(settings.LOGGING)

logger = logging.getLogger(__name__)

ws_port = settings.WEBSOCKET_PORT

define('port', type=int, default=ws_port)
tornado.options.parse_command_line()


def main():

    logger = logging.getLogger(__name__)
    tornado_app = Application(
        [
            (r'/ws/(?P<obj_type>[\w]+)/(?P<obj_id>[\d]+)/$', SocketHandler),
        ], debug=False)
    start_listener()
    logger.info("Tornado websocket server started on port {0}".format(ws_port))
    server = HTTPServer(tornado_app)
    server.listen(options.port)
    try:
        IOLoop.instance().start()
    except KeyboardInterrupt:
        logger.warn("Keyboard Interrupt")
        IOLoop.instance().stop()

if __name__ == '__main__':
    main()

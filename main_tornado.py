import logging
from urlparse import urlparse

from django.conf import settings
import django.core.handlers.wsgi

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.wsgi
from tornado.options import options, define


from facile_backlog.websockets import SocketHandler, start_listener

logger = logging.getLogger(__name__)

ws_url = urlparse(settings.WEBSOCKET_URL)

define('port', type=int, default=ws_url.port)
tornado.options.parse_command_line()


def main():

    logger = logging.getLogger(__name__)
    wsgi_app = tornado.wsgi.WSGIContainer(
        django.core.handlers.wsgi.WSGIHandler())
    tornado_app = tornado.web.Application(
        [
            (r'/ws/(?P<obj_type>[\w]+)/(?P<obj_id>[\d]+)/$', SocketHandler),
            (r'.*', tornado.web.FallbackHandler, dict(fallback=wsgi_app)),
        ], debug=True)
    start_listener()
    logger.info("Tornado server starting on port {0}".format(ws_url.port))
    server = tornado.httpserver.HTTPServer(tornado_app)
    server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()

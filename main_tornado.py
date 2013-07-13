from tornado.options import options, define
import django.core.handlers.wsgi
import logging
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.wsgi

from facile_backlog.websockets import SocketHandler


define('port', type=int, default=8000)
tornado.options.parse_command_line()


def main():

    logger = logging.getLogger(__name__)
    wsgi_app = tornado.wsgi.WSGIContainer(
        django.core.handlers.wsgi.WSGIHandler())
    tornado_app = tornado.web.Application(
        [
            ('/ws', SocketHandler),
            ('.*', tornado.web.FallbackHandler, dict(fallback=wsgi_app)),
        ], debug=True)
    logger.info("Tornado server starting...")
    server = tornado.httpserver.HTTPServer(tornado_app)
    server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()

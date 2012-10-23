# Tornado imports
import uuid
import base64
import tornado.ioloop
import tornado.options
import tornado.web
import os, sys
from tornado.options import define, options
from tornado.web import url
import tornado.httpserver
import logging.config
import configparser
from handlers import handlers_module

#logging.basicConfig(filename='example.log',level=logging.INFO)
logging.config.fileConfig('logging.conf')
define("port", default=8888, type=int)
define("config_file", default="app_config.yml", help="app_config file")

# Application class
class Application(tornado.web.Application):
    def __init__(self, **overrides):
        #self.config = self._get_config()
        handlers = [
                url(r'/', handlers_module.MainHandler, name='index'),
                url(r'/findPrefix', handlers_module.PrefixHandler, name='prefix'),
                url(r'/findPath', handlers_module.SearchHandler, name='path'),
                url(r'/findSubject', handlers_module.LookupHandler, name = 'subject'),
                url(r'/findCachedPath', handlers_module.CachedPathHandler, name = 'cached_paths'),
                url(r'/getDescription', handlers_module.CacheLookupHandler, name = 'get'),
                url(r'/getAnalysis', handlers_module.AnalysisHandler, name = 'analysis')
        ]

        #xsrf_cookies is for XSS protection add this to all forms: {{ xsrf_form_html() }}
        settings = {
            'static_path': os.path.join(os.path.dirname(__file__), 'static'),
            'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
            "cookie_secret":    base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes),
            'xsrf_cookies': False,
            'debug':True,
            'log_file_prefix':"tornado.log",
        }

        tornado.web.Application.__init__(self, handlers, **settings) # debug=True ,

# to redirect log file run python with : --log_file_prefix=mylog
def main():
    tornado.options.parse_command_line()
#    m_http_server = tornado.httpserver.HTTPServer(Application())
#    m_http_server.listen(options.port)
#    tornado.ioloop.IOLoop.instance().start()
    sockets = tornado.netutil.bind_sockets(options.port)
    if not 'win' in sys.platform:
        tornado.process.fork_processes(4, 0)
    server = tornado.httpserver.HTTPServer(Application())
    server.add_sockets(sockets)
    tornado.ioloop.IOLoop.instance().start()
    logging.getLogger('root').info ("Server running on:"+sys.platform)

if __name__ == '__main__':
    main()
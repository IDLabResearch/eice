# Tornado imports
import uuid
import base64
import tornado.ioloop
import tornado.options
import tornado.web
import os, sys, time, signal
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
MAX_WAIT_SECONDS_BEFORE_SHUTDOWN = 3


# Application class
class Application(tornado.web.Application):
    def __init__(self, **overrides):
        #self.config = self._get_config()
        handlers = [
                url(r'/', handlers_module.MainHandler, name='index'),
                url(r'/prefixes', handlers_module.PrefixHandler, name='prefixes'),
                url(r'/paths', handlers_module.SearchHandler, name='paths'),
                url(r'/subjects', handlers_module.LookupHandler, name = 'subjects'),
                url(r'/cached_paths', handlers_module.CachedPathHandler, name = 'cached_paths'),
                url(r'/descriptions', handlers_module.CacheLookupHandler, name = 'descriptions'),
                url(r'/analysis', handlers_module.AnalysisHandler, name = 'analysis'),
                url(r'/metrics', handlers_module.MetricHandler, name = 'metrics'),
                url(r'/stored_path', handlers_module.StoredPathHandler, name = 'stored_path'),
                url(r'/visualization', handlers_module.VisualizationHandler, name='visualization'),
                url(r'/neighbours', handlers_module.NeighbourLookupHandler, name='neighbours'),
                url(r'/nodedata.json', handlers_module.NodeDataHandler, name='nodedata'),
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

server = None

def sig_handler(sig, frame):
    logging.warning('Caught signal: %s', sig)
    tornado.ioloop.IOLoop.instance().add_callback(shutdown)
 
def shutdown():
    logging.info('Stopping http server')
    server.stop()
 
    logging.info('Will shutdown in %s seconds ...', MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)
    io_loop = tornado.ioloop.IOLoop.instance()
 
    deadline = time.time() + MAX_WAIT_SECONDS_BEFORE_SHUTDOWN
 
    def stop_loop():
        now = time.time()
        if now < deadline and (io_loop._callbacks or io_loop._timeouts):
            io_loop.add_timeout(now + 1, stop_loop)
        else:
            io_loop.stop()
            logging.info('Shutdown')
    stop_loop()

# to redirect log file run python with : --log_file_prefix=mylog
def main():
    tornado.options.parse_command_line()
#    m_http_server = tornado.httpserver.HTTPServer(Application())
#    m_http_server.listen(options.port)
#    tornado.ioloop.IOLoop.instance().start()
    sockets = tornado.netutil.bind_sockets(options.port)
    if not 'win' in sys.platform:
        tornado.process.fork_processes(8, 0)
    server = tornado.httpserver.HTTPServer(Application())
    server.add_sockets(sockets)
    tornado.ioloop.IOLoop.instance().start()
    logging.getLogger('root').info ("Server running on:"+sys.platform)

if __name__ == '__main__':
    main()
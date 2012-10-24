import tornado
import ujson
import signal
import time, sys
from sindice import typeahead, search,resourceretriever
import sys, traceback,logging
from sindice import cached_pathfinder
import handlers.time_out
from handlers.time_out import TimeoutException

logger = logging.getLogger('handler')

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Pathfinding Service Version 24-10-2012(a) running on %s" % sys.platform)

class AnalysisHandler(MainHandler):
    def initialize(self):
        self.cpf = cached_pathfinder.CachedPathFinder()
        self.cpf.buildMatrix()
        
    def get(self):
        file = self.cpf.visualize()
        f = open(file, "rb").read()
        self.set_header("Content-Type", "image/png")
        self.write(f)
        self.finish()

class CacheLookupHandler(MainHandler):
    
    def get(self):
        uris = self.get_argument("uri", "")
        items = uris.split(",")
        responses = dict()
        for item in items: 
            try:
                uri = item.strip('<>')
                r =  resourceretriever.describeResource(q)
                responses[uri] = r
            except:
                self.set_status(500)
                responses['error'] = 'Something went wrong x( Check the log files for more information.'
                logger.error()
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")
        self.set_header("charset", "utf8")
        #responses = sorted(responses, key=responses.__getitem__, reverse=True)
        self.write('{0}'.format(ujson.dumps(responses)))
        self.finish()
        
class PrefixHandler(MainHandler):

    def get(self):
        q = self.get_argument("query", "")
        #callback = self.get_argument("callback", "")
        try:
            r =  typeahead.dbPediaPrefix(q)
        except AttributeError:
            r = []
            self.set_status(404)
            logger.info( 'Invalid argument. Please check the provided argument. Check the server log files if error persists.')
            logger.error (sys.exc_info())
        except:
            self.set_status(500)
            r = 'Something went wrong. Check the server log files for more information.'
        #self.render("login.html", notification=self.get_argument("notification","") )
        response = ujson.dumps(r)
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")
        self.set_header("charset", "utf8")
        self.write('{0}'.format(response))
        #self.write('{0}({1})'.format(callback, response))
        self.finish()
        
class LookupHandler(MainHandler):
    
    def get(self):
        label = self.get_argument("label", "")
        logger.debug(label)
        type = self.get_argument("type", "")
        labels = label.split(",")
        logger.debug(labels)
        responses = dict()
        for label in labels: 
            try:
                uri = resourceretriever.dbPediaLookup(label, type)['uri'].strip('<>"')
                links = resourceretriever.dbPediaLookup(label, type)['links']
                responses[uri] = links
            except:
                self.set_status(500)
                responses['error'] = 'Something went wrong x( Check the log files for more information.'
                logger.error(sys.exc_info())
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")
        self.set_header("charset", "utf8")
        #responses = sorted(responses, key=responses.__getitem__, reverse=True)
        self.write('{0}'.format(ujson.dumps(responses)))
        self.finish()
     
class CachedPathHandler(MainHandler):   
    def initialize(self):
        self.cpf = cached_pathfinder.CachedPathFinder()
        
    def get(self): 
        destination = self.get_argument("destination", "")
        r = dict()
        try:
            r = self.cpf.getPaths(destination)
        except:
            self.set_status(500)
            logger.error (sys.exc_info())
            r['error'] = 'Something went wrong. Check the server log files for more information. Do not use quotes.'
        response = ujson.dumps(r)
        self.write(response)
        self.finish()
     
class SearchHandler(MainHandler):

    def get(self):
        source = self.get_argument("from", "")
        destination = self.get_argument("to", "")
        r = dict()
        try:
            with handlers.time_out.time_limit(60):
                r = search.search(source,destination)
        except TimeoutException:
            self.set_status(503)
            r = 'Your process was killed after 60 seconds, sorry! x( Try again' 
        except AttributeError:
            self.set_status(400)
            logger.error (sys.exc_info())
            r = 'Invalid arguments :/ Check the server log files if problem persists.'
        except:
            self.set_status(500)
            logger.error (sys.exc_info())
            r = 'Something went wrong x( Check the server log files for more information.'
            
        #self.render("login.html", notification=self.get_argument("notification","") )
        response = ujson.dumps(r)
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")
        self.set_header("charset", "utf8")
        self.write(response)
        self.finish()
            

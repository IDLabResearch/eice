import tornado
import ujson
import signal
import time, sys
from sindice import typeahead, search,resourceretriever
import sys, traceback,logging
from sindice import cached_pathfinder
import handlers.time_out
from handlers.time_out import TimeoutException

logger = logging.getLogger('root')

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Pathfinding Service Version 23-10-2012(b) running on %s" % sys.platform)

class CacheLookupHandler(MainHandler):
    def post(self):
        items = ujson.loads(self.request.body)
        responses = dict()
        for item in items: 
            try:
                q = item['q'].strip('<>')
                r =  resourceretriever.describeResource(q)
                responses[q] = r
            except:
                self.set_status(500)
                responses['error'] = 'Something went wrong x( Check the log files for more information.'
                logger.error()
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")
        self.set_header("charset", "utf8")
        #responses = sorted(responses, key=responses.__getitem__, reverse=True)
        self.write('{0}'.format(ujson.dumps(responses)))
        
    def get(self):
        q = self.get_argument("q", "")
        #callback = self.get_argument("callback", "")
        try:
            r =  resourceretriever.describeResource(q)
        except AttributeError:
            self.set_status(400)
            r = []
            logger.info( 'Invalid argument. Please check the provided argument. Check the server log files if error persists.')
            logger.error (sys.exc_info())
        except:
            self.set_status(500)
            r = 'Something went wrong. Check the server log files for more information.'
        if not r:
            r = 'Resource not found %s, sorry. Try again later, update the index or look for something else.' % q
            self.set_status(404)
        
        #self.render("login.html", notification=self.get_argument("notification","") )
        response = ujson.dumps(r)
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")
        self.set_header("charset", "utf8")
        self.write('{0}'.format(response))
        #self.write('{0}({1})'.format(callback, response))
        
class PrefixHandler(MainHandler):

    def get(self):
        q = self.get_argument("q", "")
        #callback = self.get_argument("callback", "")
        try:
            r =  typeahead.dbPediaPrefix(q)
        except AttributeError:
            r = []
            self.set_status(400)
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
        
class LookupHandler(MainHandler):
    
    def post(self):
        items = ujson.loads(self.request.body)
        responses = dict()
        for item in items: 
            try:
                o = item['object_value'].strip('"')
                if 'type' in item:
                    t = item['type'].strip('"')
                else:
                    t = ""
                uri = resourceretriever.dbPediaLookup(o, t)['uri'].strip('<>')
                links = resourceretriever.dbPediaLookup(o, t)['links']
                responses[uri] = links
            except:
                self.set_status(500)
                responses['error'] = 'Something went wrong x( Check the log files for more information.'
                logger.error()
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")
        self.set_header("charset", "utf8")
        #responses = sorted(responses, key=responses.__getitem__, reverse=True)
        self.write('{0}'.format(ujson.dumps(responses)))
        
        
    def get(self):
        #p = self.get_argument("property_uri", "")
        o = self.get_argument("object_value", "")
        t = self.get_argument("type", "")
        #callback = self.get_argument("callback", "")
        response = dict()
        r = dict()

        try:
            r = resourceretriever.dbPediaLookup(o.strip('"'), t.strip('"'))
            uri = r['uri'].strip('<>')
            response[uri] = r['links']
        except AttributeError as error:
            self.set_status(400)
            response['error'] = 'Invalid argument. Please check the provided argument. Check the server log files if error persists.'
            logger.error (error)
            
       
        if not 'uri' in r:
            try:
                response = resourceretriever.sindiceMatch(o, t)
            except:
                self.set_status(500)
                logger.error (sys.exc_info())
                response['error'] = 'Something went wrong. Check the server log files for more information. Do not use quotes.'

        
        if o == "":
            self.set_status(400)
            response['error'] = 'Please provide an object_value parameter.'
            
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")
        self.set_header("charset", "utf8")
        self.write('{0}'.format(ujson.dumps(response)))
        #self.write('{0}({1})'.format(callback, ujson.dumps(response)))
     
class CachedPathHandler(MainHandler):   
    def get(self):
        cpf = cached_pathfinder.CachedPathFinder()
        destination = self.get_argument("d", "")
        r = dict()
        try:
            r = cpf.getPaths(destination)
        except:
            self.set_status(500)
            logger.error (sys.exc_info())
            r['error'] = 'Something went wrong. Check the server log files for more information. Do not use quotes.'
        response = ujson.dumps(r)
        self.write(response)
            
     
class SearchHandler(MainHandler):

    def get(self):
        source = self.get_argument("from", "")
        destination = self.get_argument("to", "")

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
            logger.error (traceback.format_stack())
            r = 'Something went wrong x( Check the server log files for more information.'
            
        #self.render("login.html", notification=self.get_argument("notification","") )
        response = ujson.dumps(r)
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")
        self.set_header("charset", "utf8")
        self.write(response)
        self.finish()
            

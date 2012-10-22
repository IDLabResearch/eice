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
        self.write("Pathfinding Service Version 19-10-2012 running on %s" % sys.platform)
        
class PrefixHandler(MainHandler):

    def get(self):
        q = self.get_argument("q", "")
        #callback = self.get_argument("callback", "")
        try:
            r =  typeahead.dbPediaPrefix(q)
        except AttributeError:
            r = []
            logger.info( 'Invalid argument. Please check the provided argument. Check the server log files if error persists.')
            logger.error (sys.exc_info())
        except:
            r = 'Something went wrong. Check the server log files for more information.'
        #self.render("login.html", notification=self.get_argument("notification","") )
        response = ujson.dumps(r)
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")
        self.set_header("charset", "utf8")
        self.write('{0}'.format(response))
        #self.write('{0}({1})'.format(callback, response))
        
class LookupHandler(MainHandler):

    def get(self):
        #p = self.get_argument("property_uri", "")
        o = self.get_argument("object_value", "")
        t = self.get_argument("type", "")
        #callback = self.get_argument("callback", "")
        response = dict()
        try:
            r = resourceretriever.dbPediaLookup(o.strip('"'), t.strip('"'))
            uri = r['uri'].strip('<>')
            response['uri'] = uri
            wikiPageWikiLinks = r['wikiPageWikiLinks'].strip('<>')
            response['wikiPageWikiLinks'] = wikiPageWikiLinks
        except AttributeError as error:
            response['error'] = 'Invalid argument. Please check the provided argument. Check the server log files if error persists.'
            logger.error (error)
            
       
        if not 'uri' in response:
            try:
                response = resourceretriever.sindiceMatch(o, t)
            except:
                    logger.error (sys.exc_info())
                    response['error'] = 'Something went wrong. Check the server log files for more information. Do not use quotes.'

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
            logger.error (sys.exc_info())
            r['error'] = 'Something went wrong. Check the server log files for more information. Do not use quotes.'
        response = ujson.dumps(r)
        self.write(response)
            
     
class SearchHandler(MainHandler):

    def get(self):
        s1 = self.get_argument("s1", "")
        s2 = self.get_argument("s2", "")

        try:
            with handlers.time_out.time_limit(60):
                r = search.search(s1,s2)
        except TimeoutException:
            r = 'Your process was killed after 60 seconds, sorry! x(' 
        except AttributeError:
            logger.error (sys.exc_info())
            r = 'Invalid arguments :/ Check the server log files if problem persists.'
        except:
            logger.error (traceback.format_stack())
            r = 'Something went wrong x( Check the server log files for more information.'
            
        #self.render("login.html", notification=self.get_argument("notification","") )
        response = ujson.dumps(r)
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")
        self.set_header("charset", "utf8")
        self.write(response)
        self.finish()
            

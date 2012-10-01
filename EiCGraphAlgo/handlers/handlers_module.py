import tornado
import ujson
from sindice import typeahead, search,resourceretriever
import sys, traceback,logging

logger = logging.getLogger('root')

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")
        
class PrefixHandler(MainHandler):

    def get(self):
        q = self.get_argument("q", "")
        try:
            r =  typeahead.dbPediaPrefix(q)
        except AttributeError:
            r = 'Invalid argument. Please check the provided argument. Check the server log files if error persists.'
            logger.error (sys.exc_info())
        except:
            r = 'Something went wrong. Check the server log files for more information.'
        #self.render("login.html", notification=self.get_argument("notification","") )
        response = ujson.encode(r)
        self.write(response)
        
class SindiceHandler(MainHandler):

    def get(self):
        #p = self.get_argument("property_uri", "")
        o = self.get_argument("object_value", "")
        t = self.get_argument("type", "")
        
        try:
            r =  resourceretriever.sindiceMatch(o, t)
        except AttributeError:
            r = 'Invalid argument. Please check the provided argument. Check the server log files if error persists.'
            logger.error (sys.exc_info())
        except:
            logger.error (sys.exc_info())
            r = 'Something went wrong. Check the server log files for more information.'
        #self.render("login.html", notification=self.get_argument("notification","") )
        response = ujson.encode(r)
        self.write(response)
        
class SearchHandler(MainHandler):

    def get(self):
        s1 = self.get_argument("s1", "")
        s2 = self.get_argument("s2", "")
        
        try:
            r = search.search(s1,s2)
        except AttributeError:
            logger.error (sys.exc_info())
            r = 'Invalid arguments :/ Check the server log files if problem persists.'
        except:
            logger.error (traceback.format_stack())
            r = 'Something went wrong x( Check the server log files for more information.'
            
        #self.render("login.html", notification=self.get_argument("notification","") )
        response = ujson.encode(r)
        self.write(response)

import tornado
import ujson
from sindice import typeahead, search
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
            r = 'Invalid argument'
            print (sys.exc_info())
        except:
            r = 'Something went wrong'
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
            print (sys.exc_info())
            r = 'Invalid arguments :/'
            
        #self.render("login.html", notification=self.get_argument("notification","") )
        response = ujson.encode(r)
        self.write(response)

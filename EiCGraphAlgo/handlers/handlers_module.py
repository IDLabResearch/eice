import tornado
import ujson
import signal
import time, sys
from sindice import typeahead, search,resourceretriever,graph,randompathgenerator
import sys, traceback,logging
from sindice import cached_pathfinder
import handlers.time_out
from handlers.time_out import TimeoutException

logger = logging.getLogger('handler')

class MainHandler(tornado.web.RequestHandler):
    
    def get(self):
        self.write("Pathfinding Service Version 29-10-2012 running on %s" % sys.platform)
        self.finish()
        
class NodeDataHandler(MainHandler):
    
    def initialize(self):
        self.cpf = cached_pathfinder.CachedPathFinder()
    
    def get(self):
        response = ujson.dumps(self.cpf.getNodeData())
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")
        self.write(response)
        self.finish()

class VisualizationHandler(MainHandler):
    def get(self):
        self.render("index.html")

class AnalysisHandler(MainHandler):
    
    def initialize(self):
        self.cpf = cached_pathfinder.CachedPathFinder()
        self.cpf.buildMatrix()
        
    def get(self):
        file = self.cpf.visualize()
        f = open(file, "rb").read()
        self.write(f)
        self.set_header("Content-Type", "image/png")
        self.finish()

class CacheLookupHandler(MainHandler):
    
    def get(self):
        uris = self.get_argument("uri", "")
        items = uris.split(",http://")
        responses = dict()
        for item in items: 
            try:
                if not 'http://' in item:
                    uri = 'http://%s' % item.strip('<>')
                else:
                    uri = item.strip('<>')
                    
                r =  resourceretriever.describeResource(uri)
                responses[uri] = r
            except:
                responses[uri] = {}
                logger.error(sys.exc_info())
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
        responses = []
        for label in labels: 
            try:
                uri = resourceretriever.dbPediaLookup(label, type)['uri'].strip('<>"')
                links = resourceretriever.dbPediaLookup(label, type)['links']
                responses.append({ 'label': label, 'uri': uri, 'connectivity': links })
            except:
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
        source = randompathgenerator.randomSourceAndDestination()['source'] 
        destination = self.get_argument("destination", "")
        r = dict()
        try:
            r = self.cpf.getPaths(destination,source)
        except:
            self.set_status(500)
            logger.error (sys.exc_info())
            r['error'] = 'Something went wrong. Check the server log files for more information. Do not use quotes.'
        response = ujson.dumps(r)
        self.write(response)
        self.finish()
     
class SearchHandler(MainHandler):
    def initialize(self):
        self.cpf = cached_pathfinder.CachedPathFinder()
        
    def get(self):
        source = self.get_argument("from", "")
        destination = self.get_argument("to", "")
        r = dict()
        try:
            with handlers.time_out.time_limit(60):
                r = search.search(source,destination)
                if not r['path']:
                    logger.info('Using fallback using random hubs, because no path directly found')
                    path_between_hubs = False
                    while not path_between_hubs:
                        hubs = randompathgenerator.randomSourceAndDestination()
                        path_between_hubs = search.search(hubs['source'],hubs['destination'])
                        path_to_hub_source = search.search(source,hubs['source'])
                        path_to_hub_destination = search.search(hubs['destination'],destination)
                        if path_to_hub_source['path'] == False or path_to_hub_destination['path'] == False:
                            path_between_hubs = False
                            r['execution_time'] += path_to_hub_source['execution_time'] + path_to_hub_destination['execution_time']
                    r['source'] = source
                    r['destination'] = destination
                    r['execution_time'] += path_to_hub_source['execution_time'] + path_between_hubs['execution_time'] + path_to_hub_destination['execution_time']
                    r['path'] = list()
                    r['path'].extend(path_to_hub_source['path'][:-1])
                    r['path'].extend(path_between_hubs['path'])
                    r['path'].extend(path_to_hub_destination['path'][1:])
                        
        except TimeoutException:
            self.set_status(503)
            r = 'Your process was killed after 60 seconds, sorry! x( Try again' 
        except AttributeError:
            self.set_status(400)
            logger.error (sys.exc_info())
            r = 'Invalid arguments :/ Check the server log files if problem persists.'
        except:
            self.set_status(404)
            logger.error (sys.exc_info())
            r = 'Something went wrong x( Probaly either the start or destination URI is a dead end. Check the server log files for more information.'
            
        #self.render("login.html", notification=self.get_argument("notification","") )
        
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")
        self.set_header("charset", "utf8")
        self.write(ujson.dumps(r))
        self.finish()
            
import tornado
from mako.lookup import TemplateLookup
import ujson
import signal, os
import time, sys
from core import typeahead,graph,randompath,resourceretriever
import sys, traceback,logging
from core import cached_pathfinder
import handlers.time_out
from handlers.time_out import TimeoutError
import generateplots
from core.resourceretriever import Resourceretriever
from core.search import Searcher, DeepSearcher
import core.search_gt as sgt
from multiprocessing import Process, Queue


logger = logging.getLogger('handler')

class MainHandler(tornado.web.RequestHandler):
    
    def get(self):
        logger.info("Pathfinding Service Version 20130710.1 running on %s" % sys.platform)
        self.render('landing.html')

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
            
class MetricHandler(MainHandler):       
    def get(self):
        update = self.get_argument("update", False)
        if not update:
            pass
        else:
            generateplots.generatePlots()
        self.render("metric.html")

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
    
    def initialize(self):
        self.resourceretriever = Resourceretriever()
        
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
                    
                r =  self.resourceretriever.describeResource(uri)
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

class NeighbourLookupHandler(MainHandler):
    
    def initialize(self):
        #self.resourceretriever = Resourceretriever()
        self.r = dict()

    def get(self):
        uris = self.get_argument("uri", "")
        items = uris.split(",http://")
        responses = dict()
        #print (items)
        
        def retrieve_neighbours(q):
            logger.debug ('Neighbourlookup started %s' % uris)
            resR = resourceretriever.Resourceretriever()
            for item in items: 
                try:
                    if not 'http://' in item:
                        uri = 'http://%s' % item.strip('<>')
                    else:
                        uri = item.strip('<>')
                    print(uri)  
                    responses[uri] = resR.getResource(uri)
                except:
                    responses[uri] = {}
                    logger.error(sys.exc_info())
            logger.debug ('Neihgbour lookup finished %s' % uris)
            q.put(responses)
            
        q = Queue()
        p = Process(target=retrieve_neighbours, args=(q,))
        p.start()

        p.join(30)
        if p.is_alive():
            logger.warning ('Terminating process')
            p.terminate()
            logger.warning('No neighbours found in 30 seconds.')
            self.set_status(503)
            self.r = "Sorry, no neighbours found in 30 seconds. :( Check the log files for more information."
        else:
            self.r = q.get()
                
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")
        self.set_header("charset", "utf8")
        #responses = sorted(responses, key=responses.__getitem__, reverse=True)
        self.write('{0}'.format(ujson.dumps(self.r)))
        self.finish()

class DbPediaPrefixHandler(MainHandler):
    def initialize(self):
        self.th = typeahead.TypeAhead()
        
    def get(self):
        q = self.get_argument("query", "")
        #callback = self.get_argument("callback", "")
        try:
            r =  self.th.dbPediaPrefix(q)
            #r=typeahead.prefix(q)
        except AttributeError:
            r = []
            self.set_status(404)
            logger.info( 'Invalid argument. Please check the provided argument. Check the server log files if error persists.')
            logger.error (sys.exc_info())
        except:
            self.set_status(500)
            logger.error (sys.exc_info())
            r = 'Something went wrong. Check the server log files for more information.'
        #self.render("login.html", notification=self.get_argument("notification","") )
        response = ujson.dumps(r)
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")
        self.set_header("charset", "utf8")
        self.write('{0}'.format(response))
        #self.write('{0}({1})'.format(callback, response))
        self.finish()
        
class PrefixHandler(MainHandler):
    def initialize(self):
        self.th = typeahead.TypeAhead()
        
    def get(self):
        q = self.get_argument("query", "")
        #callback = self.get_argument("callback", "")
        try:
            #r =  typeahead.dbPediaPrefix(q)
            r = self.th.prefix(q)
            
        except AttributeError:
            r = []
            self.set_status(404)
            logger.info( 'Invalid argument. Please check the provided argument. Check the server log files if error persists.')
            logger.error (sys.exc_info())
        except:
            self.set_status(500)
            logger.error (sys.exc_info())
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
    
    def initialize(self):
        self.resourceretriever = Resourceretriever()
        
    def get(self):
        label = self.get_argument("label", "")
        logger.debug(label)
        type = self.get_argument("type", "")
        labels = label.split(",")
        logger.debug(labels)
        responses = []
        for label in labels: 
            try:
                entry = self.resourceretriever.dbPediaLookup(label, type)
                if 'uri' in entry and 'links' in entry:
                    uri = entry['uri'].strip('<>"')
                    links = entry['links']
                    responses.append({ 'label': label, 'uri': uri, 'connectivity': links })
            except:
                logger.error(sys.exc_info())
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")
        self.set_header("charset", "utf8")
        #responses = sorted(responses, key=responses.__getitem__, reverse=True)
        self.write('{0}'.format(ujson.dumps(responses)))
        self.finish()
     
class StoredPathHandler(MainHandler):   
    def initialize(self):
        self.cpf = cached_pathfinder.CachedPathFinder()
        
    def get(self):
        hash = self.get_argument("hash", "")
        try:
            r = self.cpf.getStoredPath(hash)
            if not r:
                r = dict()
                self.set_status(404)
                r['error'] = 'Stored path not found with hash %s. Try again with another hash.' % hash
        except:
            self.set_status(500)
            logger.error (sys.exc_info())
            r = dict()
            r['error'] = 'Something went wrong. Check the server log files for more information.'
            
        response = ujson.dumps(r)
        self.write(response)
        self.finish()

class CachedPathHandler(MainHandler):
    
    def initialize(self):
        self.cpf = cached_pathfinder.CachedPathFinder()
        
    def get(self):
        source = randompath.randomSourceAndDestination()['source'] 
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

class SearchGTHandler(MainHandler):
    
    def initialize(self):
        self.cpf = cached_pathfinder.CachedPathFinder()
        self.r = dict()
        
    def get(self):
        source = self.get_argument("from", "")
        destination = self.get_argument("to", "")
        user_context = self.get_argument("user_context", False)
        failed = False
        
        try:
            
            def main(q):
                logger.debug ('Main Search started for %s' % source)
                searcher = sgt.Searcher()
                self.r = searcher.search(source,destination,user_context=user_context)
                logger.debug ('Main Search finished for %s' % source)
                q.put(self.r)
            
            q = Queue()
            p = Process(target=main, args=(q,))
            p.start()

            p.join(90)
            if p.is_alive():
                logger.warning ('Terminating process')
                p.terminate()
                failed = True
            else:
                self.r = q.get()
                
            if failed:
                self.set_status(503)
                self.r = 'Your process was killed after 90 seconds, sorry! x( Try again'
                    
                    
        except AttributeError:
            self.set_status(400)
            logger.error (sys.exc_info())
            self.r = 'Invalid arguments :/ Check the server log files if problem persists.'
        except:
            self.set_status(404)
            logger.error (sys.exc_info())
            self.r = 'Something went wrong x( Probably either the start or destination URI is a dead end. Check the server log files for more information.'

        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")
        self.set_header("charset", "utf8")
        self.write(ujson.dumps(self.r))
        self.finish()

class SearchAllHandler(MainHandler):
    
    def initialize(self):
        self.cpf = cached_pathfinder.CachedPathFinder()
        self.r = dict()
        
    def get(self):
        source = self.get_argument("from", "")
        destination = self.get_argument("to", "")
        failed = False
        
        try:
            
            def main(q):
                logger.debug ('Main Search started for %s' % source)
                searcher = DeepSearcher()
                self.r = searcher.searchAllPaths(source,destination)
                logger.debug ('Main Search finished for %s' % source)
                q.put(self.r)
            
            q = Queue()
            p = Process(target=main, args=(q,))
            p.start()

            p.join(300)
            if p.is_alive():
                logger.warning ('Terminating process')
                p.terminate()
                logger.warning('Not all paths found in 300 seconds, terminating process.')
                failed = True
            else:
                self.r = q.get()
                
            if failed:
                self.set_status(503)
                self.r = 'Your process was killed after 300 seconds, sorry! x( Try again'
                    
        except AttributeError:
            self.set_status(400)
            logger.error (sys.exc_info())
            self.r = 'Invalid arguments :/ Check the server log files if problem persists.'
        except:
            self.set_status(404)
            logger.error (sys.exc_info())
            self.r = 'Something went wrong x( Probably either the start or destination URI is a dead end. Check the server log files for more information.'

        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")
        self.set_header("charset", "utf8")
        self.write(ujson.dumps(self.r))
        self.finish()
     
class SearchHandler(MainHandler):
    
    def initialize(self):
        self.cpf = cached_pathfinder.CachedPathFinder()
        self.r = dict()
        
    def get(self):
        source = self.get_argument("from", "")
        destination = self.get_argument("to", "")
        user_context = self.get_argument("user_context", False)
        failed = False
        
        try:
            
            def main(q):
                logger.debug ('Main Search started for %s' % source)
                searcher = Searcher()
                self.r = searcher.search(source,destination,user_context=user_context)
                logger.debug ('Main Search finished for %s' % source)
                q.put(self.r)
                
            def deep(q):
                logger.debug ('Deep Search started %s' % source)
                f = DeepSearcher()
                try:
                    self.r = f.searchDeep(source, destination, user_context=user_context)
                    self.r['execution_time'] = str(int(self.r['execution_time']) + 60000)
                except:
                    logger.error(sys.exc_info())
                    self.r = dict()
                    self.r['execution_time'] = str(90000)
                    self.r['path'] = False
                logger.debug ('Deep Search finished %s' % source)
                q.put(self.r)
            
            q = Queue()
            p = Process(target=main, args=(q,))
            p.start()

            p.join(60)
            if p.is_alive():
                logger.warning ('Terminating process')
                p.terminate()
                logger.warning('No path found in 60 seconds, starting deep search.')
                failed = True
            else:
                self.r = q.get()
                
            if failed:
                q = Queue()
                p = Process(target=deep, args=(q,))
                p.start()

                p.join(60)
                if p.is_alive():
                    logger.warning ('Terminating process')
                    p.terminate()
                    self.set_status(503)
                    self.r = 'Your process was killed after 120 seconds, sorry! x( Try again'
                else:
                    self.r = q.get()
                    
                    
        except AttributeError:
            self.set_status(400)
            logger.error (sys.exc_info())
            self.r = 'Invalid arguments :/ Check the server log files if problem persists.'
        except:
            self.set_status(404)
            logger.error (sys.exc_info())
            self.r = 'Something went wrong x( Probably either the start or destination URI is a dead end. Check the server log files for more information.'

        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")
        self.set_header("charset", "utf8")
        self.write(ujson.dumps(self.r))
        self.finish()
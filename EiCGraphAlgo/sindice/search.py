from sindice import pathfinder,resourceretriever,randompath,graph,worker
import time
import gc
import logging
import pickle
import os, sys
import handlers.time_out
from handlers.time_out import TimeoutError

logger = logging.getLogger('pathFinder')
query_log = logging.getLogger('query')

blacklist = resourceretriever.blacklist
#Select source and target

# 0 Hops
#s1 = resourceretriever.dbPediaLookup("Dublin", "place")['uri']
#s2 = resourceretriever.dbPediaLookup("Ireland", "place")['uri']
# 1 Hop
#s1 = resourceretriever.sindiceFind2("<label>", '"Synthesizer"', "")['uri']
#s2 = resourceretriever.sindiceFind2("<name>", '"Guetta"', "person")['uri']
# 2 hops
#s1 = resourceretriever.dbPediaLookup("Gerry Breen", "")['uri']
#s2 = resourceretriever.dbPediaLookup("Ireland", "place")['uri']
#s1 = resourceretriever.dbPediaLookup("Elton John", "person")['uri']
#s2 = resourceretriever.dbPediaLookup("Cornish%20language", "language")['uri']
# 3 hops
# s1 = resourceretriever.dbPediaLookup("David Guetta", "person")['uri']
# s2 = resourceretriever.dbPediaLookup("France", "place")['uri']
# 4 hops
#s1 = resourceretriever.dbPediaLookup("Barack Obama", "person")['uri']
#s2 = resourceretriever.dbPediaLookup("Osama Bin Laden", "person")['uri']
# s1 = resourceretriever.dbPediaLookup("Usain Bolt", "")
# s2 = resourceretriever.dbPediaLookup("Jacques Rogge", "")
# 5 hops
#s1 = resourceretriever.dbPediaLookup("Greenwich Theatre", "")['uri']
#s2 = resourceretriever.dbPediaLookup("Ireland", "place")['uri']

def search(start,dest):
    """Searches a path between two resources start and dest

    **Parameters**
    
    start : uri
        resource to start pathfinding
    destination : uri
        destination resource for pathfinding

    **Returns**
    
    response : dictionary
        contains execution time, path if found, hash

    """
    #START
    start_time = time.clock()
    
    #Initialization
    p = pathfinder.PathFinder(start,dest)
    paths = None #Initially no paths exist
    
    #Iteration 1
    m = p.iterateMatrix(blacklist)
    if graph.pathExists(m):
        paths = graph.path(p)
    
    #Following iterations
    while True:
        if not paths == None:
            if len(paths) > 0:
                break
        
        logger.info ('=== %s-- ===' % str(p.iteration))
        gc.collect()
        m = p.iterateMatrix(blacklist)
        halt_path = time.clock()
        paths = graph.path(p)
        logger.info ('Looking for path: %s' % str(time.clock()-halt_path))
        if p.iteration == 10:
            break
    resolvedPaths = list()
    
    #FINISH
    if paths:
        for path in paths:
    #       logger.debug(path)
            resolvedPath = graph.resolvePath(path,p.getResources())
            resolvedLinks = graph.resolveLinks(resolvedPath, p.getResourcesByParent())
            formattedPath = list()
            for step in resolvedPath:
                formattedPath.append(step[1:-1])
            fullPath = dict()
            fullPath['vertices'] = formattedPath
            fullPath['edges'] = resolvedLinks
            resolvedPaths.append(fullPath)
    else:
        return {'path':False,'execution_time':int(round((time.clock()-start_time) * 1000))}
            
    #    graph.visualize(p, path=path)
    finish = int(round((time.clock()-start_time) * 1000))
    r = dict()
    r['execution_time'] = finish
    r['paths'] = resolvedPaths
    r['source'] = start
    r['destination'] = dest
    r['checked_resources'] = p.checked_resources
    r['hash'] = 'h%s' % hash('{0}{1}{2}'.format(start_time,dest,time.time()))
    r['path'] = graph.listPath(resolvedPath,p.getResourcesByParent())
    
    try:
        path = os.path.dirname(os.path.abspath(__file__))
        file = r['hash']
        pickle.dump(r,open("{0}/stored_paths/{1}.dump".format(path,file),"wb"))
    except:
        logger.warning('could not log and store path between {0} and {1}'.format(start_time,dest))
        logger.error(sys.exc_info())
    query_log.info(r)
    logger.debug(r)
    result = dict()
    result['path'] = r['path']
    result['hash'] = r['hash']
    result['execution_time'] = r['execution_time']
    return result

#r = search(start,dest)
#
#p = r['path']
#time = r['execution_time']
#
#print (str(time)+' ms')
#print (p)
#
#if paths:
#    graph.visualize(p, path=path)
#else:
#    graph.visualize(p)

def searchFallback(source,destination):
    worker.startQueue(searcher, 3)
    resp = dict()
    logger.info('Using fallback using random hubs, because no path directly found')
    path_between_hubs = False
    while not path_between_hubs:
        start = time.clock()
        worker_output = dict()
        hubs = randompath.randomSourceAndDestination()
        worker.getQueue(searcher).put([hubs['source'],hubs['destination'],worker_output,'path_between_hubs'])
        worker.getQueue(searcher).put([source,hubs['source'],worker_output,'path_to_hub_source'])
        worker.getQueue(searcher).put([hubs['destination'],destination,worker_output,'path_to_hub_destination'])
        worker.getQueue(searcher).join()
        path_between_hubs = worker_output['path_between_hubs']
        path_to_hub_source = worker_output['path_to_hub_source']
        path_to_hub_destination = worker_output['path_to_hub_destination']
        if path_to_hub_source['path'] == False or path_to_hub_destination['path'] == False:
            path_between_hubs = False
            gc.collect()
            time.sleep(1)
    
    resp['execution_time'] = str(int(round((time.clock()-start) * 1000)))
    resp['source'] = source
    resp['destination'] = destination
    resp['path'] = list()
    resp['path'].extend(path_to_hub_source['path'][:-1])
    resp['path'].extend(path_between_hubs['path'])
    resp['path'].extend(path_to_hub_destination['path'][1:])
    del worker.q[searcher]
    return resp

def searcher():
    q = worker.getQueue(searcher)
    while True:
        items = q.get()
        if len(items) == 4:
            source = items[0]
            destination = items[1]
            try:
                items[2][items[3]] = search(source,destination)
            except:
                items[2][items[3]] = dict()
                items[2][items[3]]['path'] = False
                logger.error(sys.exc_info())
                logger.error('path between {0} and {1} not found.'.format(source, destination))
        else:
            pass
        q.task_done()
        
def fallback_searcher():
    q = worker.getQueue(fallback_searcher)
    while True:
        items = q.get()
        if len(items) == 4:
            source = items[0]
            destination = items[1]
            items[2][items[3]] = searchFallback(source,destination)
        else:
            pass
        q.task_done()
             


#print (searchFallback('http://dbpedia.org/resource/Brussels','http://dbpedia.org/resource/Belgium'))
#print (search('http://dbpedia.org/resource/Brussels','http://dbpedia.org/resource/Belgium'))

'''
Created on 11-sep.-2012

@author: ldevocht
'''
from sindice import pathfinder,resourceretriever,graph
import time
import gc
import logging
import pickle
import os, sys

logger = logging.getLogger('pathFinder')
query_log = logging.getLogger('query')

#Define properties to ignore:
blacklist = frozenset(['<http://dbpedia.org/ontology/wikiPageWikiLink>',
             '<http://dbpedia.org/property/title>',
             '<http://dbpedia.org/ontology/abstract>',
             '<http://xmlns.com/foaf/0.1/page>',
             '<http://dbpedia.org/property/wikiPageUsesTemplate>',
             '<http://dbpedia.org/ontology/wikiPageExternalLink>',
             #'<http://dbpedia.org/ontology/wikiPageRedirects>',
             '<http://purl.org/dc/elements/1.1/description>',
             '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>',
             '<http://www.w3.org/2002/07/owl#sameAs>',
             '<http://purl.org/dc/terms/subject>',
             '<http://dbpedia.org/property/website>',
             '<http://dbpedia.org/property/label>',
             '<http://xmlns.com/foaf/0.1/homepage>'
             '<http://dbpedia.org/ontology/wikiPageDisambiguates>',
             '<http://dbpedia.org/ontology/thumbnail>',
             '<http://xmlns.com/foaf/0.1/depiction>'
             ])

#Select source and target

# 0 Hops
#s1 = resourceretriever.dbPediaLookup("Dublin", "place")['uri']
#s2 = resourceretriever.dbPediaLookup("Ireland", "place")['uri']
# 1 Hop
# s1 = resourceretriever.sindiceFind2("<label>", '"Synthesizer"', "")
# s2 = resourceretriever.sindiceFind2("<name>", '"Guetta"', "person")
# 2 hops
# s1 = resourceretriever.dbPediaLookup("Gerry Breen", "")
# s2 = resourceretriever.dbPediaLookup("Ireland", "place")
# s1 = resourceretriever.dbPediaLookup("Elton John", "person")['uri']
# s2 = resourceretriever.dbPediaLookup("Cornish%20language", "language")['uri']
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

def search(s1,s2):
    #START
    start = time.clock()
    
    #Initialization
    p = pathfinder.PathFinder(s1,s2)
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
        logger.info ('Looking for path')
        paths = graph.path(p)
    
        if p.iteration == 8:
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
            
    #    graph.visualize(p, path=path)
    finish = int(round((time.clock()-start) * 1000))
    r = dict()
    r['execution_time'] = finish
    r['paths'] = resolvedPaths
    r['source'] = s1
    r['destination'] = s2
    try:
        path = os.path.dirname(os.path.abspath(__file__))
        file = hash('{0}_{1}_{2}'.format(s1,s2,time.time()))
        pickle.dump(r,open("{0}/stored_paths/{1}.dump".format(path,file),"wb"))
    except:
        logger.warning('could not log and store path between {0} and {1}'.format(s1,s2))
    query_log.info(r)
    logger.debug(r)
    return r

#r = search(s1,s2)
#
#p = r['paths']
#time = r['execution_time']
#
##
#print (str(time)+' ms')
#print (p)
#
#if paths:
#    graph.visualize(p, path=path)
#else:
#    graph.visualize(p)

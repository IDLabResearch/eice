'''
Created on 11-sep.-2012

@author: ldevocht
'''
from sindice import pathfinder,resourceretriever,graph
import time
import gc
import logging

logger = logging.getLogger('pathFinder')

#Define properties to ignore:
blacklist = frozenset(['<http://dbpedia.org/ontology/wikiPageWikiLink>',
             '<http://dbpedia.org/property/title>',
             '<http://dbpedia.org/ontology/abstract>',
             '<http://xmlns.com/foaf/0.1/page>',
             '<http://dbpedia.org/property/wikiPageUsesTemplate>',
             '<http://dbpedia.org/ontology/wikiPageExternalLink>',
             '<http://dbpedia.org/ontology/wikiPageRedirects>'
             '<http://purl.org/dc/elements/1.1/description>',
             '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>',
             '<http://www.w3.org/2002/07/owl#sameAs>',
             '<http://purl.org/dc/terms/subject>',
             '<http://dbpedia.org/property/label>',
             '<http://dbpedia.org/ontology/wikiPageDisambiguates>'])

#Select source and target

# 0 Hops
#s1 = resourceretriever.dbPediaLookup("Dublin", "place")
#s2 = resourceretriever.dbPediaLookup("Ireland", "place")
# 1 Hop
# s1 = resourceretriever.sindiceFind2("<label>", '"Synthesizer"', "")
# s2 = resourceretriever.sindiceFind2("<name>", '"Guetta"', "person")
# 2 hops
# s1 = resourceretriever.dbPediaLookup("Gerry Breen", "")
# s2 = resourceretriever.dbPediaLookup("Ireland", "place")
# s1 = resourceretriever.dbPediaLookup("Elton John", "person")
# s2 = resourceretriever.dbPediaLookup("Cornish%20language", "language")
# 3 hops
# s1 = resourceretriever.dbPediaLookup("David Guetta", "person")
# s2 = resourceretriever.dbPediaLookup("Chicago Theatre", "place")
# 4 hops
# s1 = resourceretriever.dbPediaLookup("Barack Obama", "person")
# s2 = resourceretriever.dbPediaLookup("Osama Bin Laden", "person")
# s1 = resourceretriever.dbPediaLookup("Usain Bolt", "")
# s2 = resourceretriever.dbPediaLookup("Jacques Rogge", "")
# 5 hops
# s1 = resourceretriever.dbPediaLookup("Greenwich Theatre", "")
# s2 = resourceretriever.dbPediaLookup("Ireland", "place")

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
        paths = graph.path(p)
    
        if p.iteration == 7:
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
    logger.debug(r)
    return r

#r = search(s1,s2)

#p = r['paths']
#time = r['execution_time']

#
#print (str(time)+' ms')
#print (p)
#
#if paths:
#    graph.visualize(p, path=path)
#else:
#    graph.visualize(p)

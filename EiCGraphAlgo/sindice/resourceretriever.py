'''
Created on 13-sep.-2012

@author: ldevocht
'''
import numpy as np
import ujson
from sindice import worker
from mysolr import Solr
import urllib.request
import urllib.parse
import lxml.objectify
import logging
import sys
import configparser
import os

logger = logging.getLogger('pathFinder')
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__))+'/config.ini') 
index_server = config.get('services', 'index')
solr = Solr(index_server)

def sindiceMatch(value, kind):
    request = "http://api.sindice.com/v3/search?q={0}&fq=domain:dbpedia.org class:{1} format:RDF&format=json".format(value, kind)
    request = urllib.parse.quote(request, ':/=?<>"*&')
    logger.debug(request)
    raw_output = urllib.request.urlopen(request).read()
    
    output = ujson.loads(raw_output)
    results = output['entries']
    formatted_results = dict()
    for result in results:
        formatted_results[result['title'][0]['value']] = result['link']
    
    response = dict()
    if value in results:
        response['uri'] = formatted_results[value]
    else: 
        response['uri'] = list(output['entries'])[0]['link']
    
    return response

def sindiceFind(source, prop, value, kind):
    if kind != "":
        request = "http://api.sindice.com/v3/search?nq={0} {1} {2}&fq=-predicate:http://dbpedia.org/ontology/wikiPageWikiLink domain:dbpedia.org class:{3} format:RDF&format=json".format(source, prop, value, kind)
    else:
        request = "http://api.sindice.com/v3/search?nq={0} {1} {2}&fq=-predicate:http://dbpedia.org/ontology/wikiPageWikiLink domain:dbpedia.org format:RDF &format=json ".format(source, prop, value, kind)
    request = urllib.parse.quote(request, ':/=?<>"*&')
    logger.debug(request)
    raw_output = urllib.request.urlopen(request).read()
    output = ujson.loads(raw_output)
    link = list(output['entries'])[0]['link']
    return '<%(link)s>' % locals()

def sindiceFind2(prop, value, kind):
    return sindiceFind('*', prop, value, kind)

def dbPediaLookup(value, kind=""):
    server = config.get('services', 'lookup')
    gateway = '{0}/api/search.asmx/KeywordSearch?QueryClass={1}&QueryString={2}'.format(server,kind,value)
    request = urllib.parse.quote(gateway, ':/=?<>"*&')
    logger.debug ('Request {0}'.format(request))
    raw_output = urllib.request.urlopen(request).read()
    root = lxml.objectify.fromstring(raw_output)
    results = dict()
    for result in root.Result:
        results[result.Label[0]] = result.URI[0]

    if value in results:
        return "<%s>" % (results[value])
    else: 
        return "<%s>" % (root.Result.URI[0])

def getResource(resource):
    try:
        return getResourceLocal(resource)
    except:
        logger.warning(sys.exc_info())
        return getResourceRemote(resource)

def getResourceLocal(resource):
    source = resource.strip('<>')

    query={'nq':'<%s> * *' % source,'qt':'siren','q':'','fl':'id ntriple'}
    response = solr.search(**query)
    if response.status==200:
        nt = response.documents[0]['ntriple'].split('.\n')[:-1]
        print(nt)
        nt_cleaned = cleanResultSet(nt)
        return nt_cleaned
    
    else:
        raise
    
        

def getResourceRemote(resource):
    source = resource.strip('<>')
    request = 'http://api.sindice.com/v3/cache?pretty=true&url={0}'.format(source)
    try:
        raw_output = urllib.request.urlopen(request).read()
        cache_output = ujson.loads(raw_output)
        nt = cache_output[list(cache_output)[0]]['explicit_content']
        nt_cleaned = cleanResultSet(nt)
        return nt_cleaned
    except KeyError:
        #logger.warning ('Request not found: {0}'.format(request))
        return False
    except:
        logger.warning (sys.exc_info())
        return False
    
def getResourceLive(resource):
    source = resource.strip('<>')
    request = 'http://api.sindice.com/v2/live?url={0}&output=json'.format(source)
    try:
        raw_output = urllib.request.urlopen(request).read()
        cache_output = ujson.loads(raw_output)
        nt = cache_output['extractorResults']['metadata']['explicit']['bindings']
        nt_cleaned = formatResultSet(nt)
        return nt_cleaned
    except KeyError:
        #logger.warning ('Request not found: {0}'.format(request))
        return False
    except:
        #logger.warning (sys.exc_info())
        return False
    
def cleanResultSet(resultSet):
    nt_cleaned = dict()
    resultSet = set(resultSet)
    i = 0
    for triple in resultSet:
        triple = triple.strip(' .\n')
        triple = triple.split(' ', 2)
        triple[2] = triple[2].replace('"', '')
        nt_cleaned[i] = triple
        i += 1
    return nt_cleaned

def formatResultSet(resultSet):
    nt_cleaned = dict()
    i = 0
    for item in resultSet:
        triple = dict()
        triple[0] = item['s']['value']
        triple[1] = item['p']['value']
        triple[2] = item['o']['value']
        nt_cleaned[i] = triple
        i += 1
    return nt_cleaned
        
def extractMainResource(cleanedResultSet):
    return cleanedResultSet[0][0]

def isResource(item):               
    if '<' in item and not '^' in item:
        return True
    else:
        return False

def resourceFetcher():
    q = worker.getQueue(resourceFetcher)
    while True:
        item = q.get()
        fetchResource(item[0], item[1], item[2], item[3])
        q.task_done()
        

def addDirectedLink(source, target, predicate, resourcesByParent):
    if not target in resourcesByParent:
        resourcesByParent[target] = dict()
    resourcesByParent[target][source] = predicate

def fetchResource(resource, resourcesByParent, additionalResources, blacklist):   
    newResources = getResource(resource)
    if newResources:
        for tripleKey, triple in newResources.items():
            targetRes = triple[2]
            predicate = triple[1]
            if isResource(targetRes) and (predicate not in blacklist):
                #Add forward link  
                addDirectedLink(resource, targetRes, predicate, resourcesByParent)
                #Add backward link
                addDirectedLink(targetRes, resource, predicate, resourcesByParent)
                additionalResources.add(targetRes)      
        
def removeUnimportantResources(unimportant, resources):
    updated_resources = dict()
    for u in unimportant:
        #Never delete grandmother and grandfather, even if they become insignificant
        if u > 1: 
            del resources[u]
    i = 0
    for r in resources:
        updated_resources[i] = resources[r]
        i += 1        
    resources = updated_resources
    return resources
    
def rankToKeep(u, singularValues, threshold):
    i = 0
    for sVal in singularValues:      
        if sVal < threshold:
            return i
        i += 1

def unimportantResources(u, rank, s):
    unimportant = set()
    for i in range(rank, len(s)):
        u_abs = np.absolute (u[i])
        maxindex = u_abs.argmax()
        unimportant.add(maxindex)
    return unimportant

#print (sindiceMatch('David Guetta','person'))
#res = dbPediaLookup('David Guetta','')
#print (getResource(res))
#print(getResourceLocal('http://dbpedia.org/resource/%22Love_and_Theft%22'))
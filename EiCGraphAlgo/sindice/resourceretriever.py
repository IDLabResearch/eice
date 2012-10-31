'''
Created on 13-sep.-2012

@author: ldevocht
'''
import numpy as np
import ujson
from sindice import worker
from mysolr import Solr
from SPARQLWrapper import SPARQLWrapper, JSON
import urllib.request
import urllib.parse
import lxml.objectify
import logging
import sys
import configparser
import os

#Define properties to ignore:
blacklist = frozenset(['<http://dbpedia.org/ontology/wikiPageWikiLink>',
             '<http://dbpedia.org/property/title>',
             '<http://dbpedia.org/ontology/abstract>',
             '<http://xmlns.com/foaf/0.1/page>',
             '<http://dbpedia.org/property/wikiPageUsesTemplate>',
             '<http://dbpedia.org/ontology/wikiPageExternalLink>',
             #'<http://dbpedia.org/ontology/wikiPageRedirects>',
             '<http://dbpedia.org/ontology/wikiPageDisambiguates>',
             '<http://dbpedia.org/ontology/governmentType>',
             '<http://dbpedia.org/ontology/officialLanguage>',
             '<http://dbpedia.org/ontology/spokenIn>',
             '<http://dbpedia.org/ontology/language>',
             '<http://purl.org/dc/elements/1.1/description>',
             '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>',
             '<http://www.w3.org/2002/07/owl#sameAs>',
             '<http://purl.org/dc/terms/subject>',
             '<http://dbpedia.org/property/website>',
             '<http://dbpedia.org/property/label>',
             '<http://xmlns.com/foaf/0.1/homepage>'
             '<http://dbpedia.org/ontology/wikiPageDisambiguates>',
             '<http://dbpedia.org/ontology/thumbnail>',
             '<http://xmlns.com/foaf/0.1/depiction>',
             '<http://dbpedia.org/ontology/type>',
             '<http://dbpedia.org/ontology/related>',
             '<http://dbpedia.org/ontology/populationPlace>',
             '<http://dbpedia.org/ontology/timeZone>',
             ])


logger = logging.getLogger('pathFinder')
config = configparser.ConfigParser()

if os.path.isfile(os.path.dirname(__file__)+'/config_local.ini'):
    logger.debug('using local config file')
    config.read(os.path.join(os.path.dirname(__file__))+'/config_local.ini')
else:
    config.read(os.path.join(os.path.dirname(__file__))+'/config.ini') 
    
index_server = config.get('services', 'index')
sparql_server = config.get('services', 'sparql')
use_remote = config.get('services', 'use_remote')

try:
        sparql = SPARQLWrapper(sparql_server)
except:
        logger.error ("SPARQL Service down")
        sparql = None
        
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

def sparqlQueryByUri(uri):
    if sparql:
        query = " \
                PREFIX p: <http://dbpedia.org/property/> \
                PREFIX dbpedia: <http://dbpedia.org/resource/> \
                PREFIX category: <http://dbpedia.org/resource/Category:> \
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> \
                PREFIX dbo: <http://dbpedia.org/ontology/> \
                SELECT ?label ?abstract ?type WHERE { \
                  <%s> rdfs:label ?label . \
                  ?x rdfs:label ?label . \
                  ?x dbo:abstract ?abstract . \
                  ?x rdf:type ?type . \
                  FILTER (lang(?abstract) = \"en\") . \
                  FILTER (lang(?label) = \"en\") . \
                } LIMIT 2 \
                " % uri
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        r=dict()
        for result in results["results"]["bindings"]:
            r['label'] = result['label']['value']
            r['abstract'] = result['abstract']['value']
            r['type'] = result['type']['value']
        return r
    else:
        return False
    
def sparqlQueryByLabel(value):
    if sparql:
        query = """
                PREFIX p: <http://dbpedia.org/property/>
                PREFIX dbpedia: <http://dbpedia.org/resource/>
                PREFIX category: <http://dbpedia.org/resource/Category:>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX dbo: <http://dbpedia.org/ontology/>
                SELECT ?x (count(distinct ?y) AS ?wikiPageWikiLinks) WHERE {
                  ?x rdfs:label "%s"@en .
                  ?x dbo:wikiPageWikiLink ?y
                } ORDER BY DESC(count(distinct ?y)) LIMIT 1
                """ % value
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        r=dict()
        for result in results["results"]["bindings"]:
            r['uri'] = result['x']['value']
            r['links'] = result['wikiPageWikiLinks']['value']
        return r
    else:
        return False

def dbPediaLookup(value, kind=""):
    s = sparqlQueryByLabel(value)
    l = getResourceLocal(s['uri'].strip("<>"))
    if s and l:
        s['links'] = len(l)
        for triple in l:
            if l[triple][1] in blacklist:
                s['links'] = s['links'] - 1
    else:
        s = dbPediaIndexLookup(value, kind)
    return s



def dbPediaIndexLookup(value, kind=""):
    server = config.get('services', 'lookup')
    gateway = '{0}/api/search.asmx/KeywordSearch?QueryClass={1}&QueryString={2}'.format(server,kind,value)
    request = urllib.parse.quote(gateway, ':/=?<>"*&')
    logger.debug ('Request {0}'.format(request))
    raw_output = urllib.request.urlopen(request).read()
    root = lxml.objectify.fromstring(raw_output)
    results = dict()

    r = dict()
    klasse = "Miscelaneaous"
    for result in root.Result:
        results[result.Label[0]] = result.URI[0]

    try:
        klasse = root.Result[0].Classes.Class[0].Label[0].text
    except:
        klasse = "misc"
    
    if value in results:
        r['uri'] = "<%s>" % (results[value])
        r['label'] = value
    else: 
        r['uri'] = "<%s>" % (root.Result.URI[0])
        r['label'] = value
        
    r['type'] = klasse
        
    try:
        links = len(getResourceLocal(r['uri']))
    except:
        links = 0
        
    r['links'] = links
    

    return r

def getResource(resource):
    try:
        local = getResourceLocal(resource)
    except:
        logger.error ('connection error: could not connect to index. Check the index log files for more info.')
    if local:
        return local
    else:
        logger.warning("resource %s not in local index" % resource)        
        if use_remote == 'True':
            logger.warning("Fetching %s remotely instead" % resource)
            return getResourceRemote(resource)
        else:
            return False

def describeResource(resource):
    label='<http://www.w3.org/2000/01/rdf-schema#label>'
    abstract='<http://dbpedia.org/ontology/abstract>'
    r = getResource(resource)
    response = dict()
    if r:
        properties = dict()
        [properties.update({triple[1]:triple[2]}) for triple in r.values()]  
        if label in properties:
            response['label'] = properties[label]
        if abstract in properties:
            response['abstract'] = properties[label]
    if not r or 'label' not in response or 'abstract' not in response or 'type' not in response:
        response = sparqlQueryByUri(resource)
        
    if response['label'] and not 'type' in response:
        response['type'] = dbPediaIndexLookup(response['label'])['type']
    return response      

def getResourceLocal(resource):
    source = resource.strip('<>')

    query={'nq':'<{0}> * *'.format(source),'qt':'siren','q':'','fl':'id ntriple','timeAllowed':'50'}
    response = solr.search(**query)
    if response.status==200 and len(response.documents) > 0:
        nt = response.documents[0]['ntriple'].split('.\n')[:-1]
        nt_cleaned = cleanResultSet(nt)
        return nt_cleaned
    
    else:
        return False
    
        

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
        #logger.warning (sys.exc_info())
        logger.warning ('Resource N/A remotely: %s' % resource)
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
        

def addDirectedLink(source, target, predicate, inverse, resourcesByParent):
    if not target in resourcesByParent:
        resourcesByParent[target] = dict()
    link = dict()
    link['uri'] = predicate
    link['inverse'] = inverse
    resourcesByParent[target][source] = link

def fetchResource(resource, resourcesByParent, additionalResources, blacklist):   
    newResources = getResource(resource)
    if newResources:
        for tripleKey, triple in newResources.items():
            targetRes = triple[2]
            predicate = triple[1]
            if isResource(targetRes) and (predicate not in blacklist) and 'dbpedia' in targetRes:
                #Add forward link  
                addDirectedLink(resource, targetRes, predicate, True, resourcesByParent)
                #Add backward link
                addDirectedLink(targetRes, resource, predicate, False, resourcesByParent)
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
        
def rankToRemove(u, singularValues, threshold):
    i = 0
    for sVal in singularValues:      
        if sVal > threshold:
            return i
        i += 1

def unimportantResources(u, rank, s):
    unimportant = set()
    for i in range(rank, len(s)):
        u_abs = np.absolute (u[i])
        maxindex = u_abs.argmax()
        unimportant.add(maxindex)
    return unimportant

def importantResources(u, rank):
    important = set()
    for i in range(0, rank):
        u_abs = np.absolute (u[i])
        maxindex = u_abs.argmax()
        important.add(maxindex)
    return important

#describeResource('http://dbpedia.org/resource/Belgium')
#print (sindiceMatch('David Guetta','person'))
#res = dbPediaLookup('David Guetta','')
#print (getResource(res))
#print(getResourceLocal('http://dbpedia.org/resource/Ireland'))
#bPediaLookup('Belgium')

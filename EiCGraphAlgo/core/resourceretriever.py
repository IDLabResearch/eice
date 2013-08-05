import numpy as np
import ujson
import mysolr.compat
from mysolr.response import SolrResponse
from SPARQLWrapper import SPARQLWrapper, JSON
import urllib.request
import urllib.parse
import lxml.objectify
import logging
import sys
import configparser
import os
import rdflib
import sys
import tempfile
import requests
import time
from urllib.parse import urljoin
import requests
import re
import ujson

#Define properties to ignore:
blacklist = frozenset([
             '<http://dbpedia.org/ontology/wikiPageWikiLink>',
             '<http://dbpedia.org/property/title>',
             '<http://dbpedia.org/ontology/abstract>',
             #'<http://xmlns.com/foaf/0.1/page>',
             '<http://dbpedia.org/property/wikiPageUsesTemplate>',
             '<http://dbpedia.org/ontology/wikiPageExternalLink>',
             #'<http://dbpedia.org/ontology/wikiPageRedirects>',
             '<http://purl.org/muto/core#tagMeans>',
             '<http://dbpedia.org/ontology/wikiPageDisambiguates>',
             '<http://dbpedia.org/ontology/governmentType>',
             '<http://dbpedia.org/ontology/officialLanguage>',
             '<http://dbpedia.org/ontology/spokenIn>',
             '<http://dbpedia.org/ontology/language>',
             '<http://purl.org/dc/elements/1.1/description>',
             '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>',
             #'<http://www.w3.org/2002/07/owl#sameAs>',
             '<http://purl.org/dc/terms/subject>',
             #'<http://dbpedia.org/property/website>',
             '<http://dbpedia.org/property/label>',
             #'<http://xmlns.com/foaf/0.1/homepage>',
             '<http://dbpedia.org/ontology/wikiPageDisambiguates>',
             '<http://dbpedia.org/ontology/thumbnail>',
             '<http://xmlns.com/foaf/0.1/depiction>',
             '<http://dbpedia.org/ontology/type>',
             '<http://dbpedia.org/ontology/related>',
             '<http://dbpedia.org/ontology/populationPlace>',
             '<http://dbpedia.org/ontology/timeZone>',
             ])

valid_domains = frozenset([
                        'dbpedia',
                        'freebase',
                        'colinda',
                        'dblp',
                        'localhost'
                           ])

logger = logging.getLogger('pathFinder')
config = configparser.ConfigParser()
mappings = configparser.ConfigParser()
mappings.read(os.path.dirname(__file__)+'/mappings.conf')

if os.path.isfile(os.path.dirname(__file__)+'/config_local.ini'):
    logger.debug('using local config file')
    config.read(os.path.join(os.path.dirname(__file__))+'/config_local.ini')
else:
    config.read(os.path.join(os.path.dirname(__file__))+'/config.ini')

sparql_server = config.get('services', 'sparql')
use_remote = config.get('services', 'use_remote')
use_inverse = config.get('services', 'use_inverse')

def openSolrs():
    solrs = list()
    index_server = config.get('services', 'index_main')
    #solr = Solr(index_server)
    solrs.append(index_server)
    if config.has_option('services', 'index_second'):
        secondary_index_server = config.get('services', 'index_second')
        #solrs.append(Solr(secondary_index_server))
        solrs.append(secondary_index_server)
    if config.has_option('services','index_bu'):
        backup_index_server = config.get('services', 'index_bu')
        #solrs.append(Solr(backup_index_server))
        solrs.append(backup_index_server)
    return solrs

solrs = openSolrs()

try:
        sparql = SPARQLWrapper(sparql_server)
except:
        logger.error ("SPARQL Service down")
        sparql = None
    
print ("EiCE Server Async running on: %s :)" % sys.platform)

class Resourceretriever:
    
    def __init__(self, solrs=solrs):
        self.logger = logging.getLogger('pathFinder')
        self.config = config
        self.solrs = solrs
        self.auth = None
    
    def genUrls(self, resource):
        resource = resource.strip('<>')
        bases = []
        for solr in self.solrs:
            bases.append("%sselect?nq=<%s> * *&fl=id ntriple type&wt=json&qt=siren" % (solr,resource))
        return bases
    
    def genMultiUrls(self, resources):
        multi_urls = []
        resource_chunks = chunks(list(resources), 16)
        for resource_chunk in resource_chunks:
            queryParts = []
            for resource in resource_chunk:
                resource = resource.strip('<>!+&')
                resource = urllib.parse.quote(resource, ':\/=?<>"*')
                if not ('&' in resource or '#' in resource):
                    queryParts.append("<%s> * * OR * * <%s>" % (resource,resource))
            query = " OR ".join(queryParts)
            bases = []
            for solr in self.solrs:
                bases.append("%sselect?nq=%s&fl=id ntriple type&wt=json&qt=siren" % (solr,query))
            #for base in bases:
            #    print(len(base))
            multi_urls.append({'resources' : resource_chunk, 'urls' : bases})
        return multi_urls
    
    def processMultiResourceLocal(self, resources, resp):
        """Process subjects and predicate linking to a given URI, the URI as object in the configured local INDEX"""
        #print (resp)
        try:
            if len(resp['docs']) > 0:
                nt = ""
                for document in resp['docs']:
                    nt += document['ntriple']
                nt_cleaned = cleanMultiResultSet(nt,resources)
                return nt_cleaned
            
            else:
                return False
        except: 
            #self.logger.error('Could not fetch resource inverse %s' % resource)
            return False
    
    def genInverseUrls(self, resource):
        resource = resource.strip('<>')
        bases = []
        for solr in self.solrs:
            bases.append("%sselect?nq=* * <%s>&fl=id ntriple type&wt=json&qt=siren" % (solr,resource))
        return bases
    
    def processMultiResource(self, res, rp, resourcesByParent, additionalResources, blacklist, inverse = False):
        resources = res['resources']   
        try:
        #    if len(url) < 2048:
        #        resp = requests.get(url)
        #        if (resp.status_code == 200):
        #            resp = ujson.decode(resp.content)['response']
        #    else:
        #        urls = url.split('select?')
        #        params = urls[1].split('&')
        #        payload = {}
        #        for p in params:
        #            parts = p.split('=')
        #            payload[parts[0]] = parts[1]
        #        resp = requests.post("%sselect" % urls[0], data=payload)
        #       if (resp.status_code == 200):
        #          resp = ujson.decode(resp.content)['response']
            resp = ujson.decode(rp.content)['response']
            newResources = []
            newResources = self.processMultiResourceLocal(resources, resp)
            if newResources:
                for tripleKey, triple in newResources.items():
                    inverse = False
                    if triple[0] in resources:
                        targetRes = triple[2]
                        resource = triple[0]
                    else:
                        targetRes = triple[0]
                        resource = triple[2]
                        inverse = True
                    predicate = triple[1]
                    
                    if isResource(targetRes) and (predicate not in blacklist) and targetRes.startswith('<') and targetRes.endswith('>') and any(domain in targetRes for domain in valid_domains): #and 'dbpedia' in targetRes:
                        #Add forward link  
                        addDirectedLink(resource, targetRes, predicate, not inverse, resourcesByParent)
                        #Add backward link
                        addDirectedLink(targetRes, resource, predicate, inverse, resourcesByParent)
                        additionalResources.add(targetRes)          
        except:
            logger.error('error in retrieving %s' % resources)
            logger.error(sys.exc_info())
                    
    def processResourceLocalInverse(self,resource,response):
        """Fetch subjects and predicate linking to a given URI, the URI as object in the configured local INDEX"""
        source = resource.strip('<>')
        response = ujson.decode(response.content)['response']
        try:
            if len(response['docs']) > 0:
                nt = ""
                for document in response['docs']:
                    nt += document['ntriple']
                nt_cleaned = cleanInversResultSetFast(nt,source)
                return nt_cleaned
        except: 
            #self.logger.error('Could not fetch resource inverse %s' % resource)
            return False  
                    
    def getResource(self, resource, use_inverse=True):
        try:
            urls = self.genUrls(resource)
            response = dict()
            #print ('getting resource local')
            rs = (requests.get(u) for u in urls)
            resps = rs
            for resp in resps:
                local = self.processResourceLocal(resource, resp)
                if local:
                    base = len(response)
                    
                    for key in local:
                        response[int(key)+base] = local[key]
                
            if use_inverse == 'True' and len(response) > 0:
                inv_urls = self.genInverseUrls(resource)
                rs = (requests.get(u) for u in inv_urls)
                resps = rs
                for resp in resps:
                    inverse = self.processResourceLocalInverse(resource, resp)
                    if inverse:
                        base = len(response)
                        for key in inverse:
                            response[int(key)+base] = inverse[key]
        except:
            self.logger.error ('connection error: could not connect to index. Check the index log files for more info.')
            print(sys.exc_info())
            response = False
            
        return response

    def processResourceLocal(self,resource,response):
        """Fetch properties and children from a resource given a URI in the configured local INDEX"""
        source = resource.strip('<>')
        response = ujson.decode(response.content)['response']
        try:
            if len(response['docs']) > 0:
                nt = response['docs'][0]['ntriple'].split('.\n')[:-1]
                nt_cleaned = cleanResultSet(nt)
                tl = list()
                tl.append('<%s>' % resource)
                tl.append('<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>')
                tl.append(response['docs'][0]['type'].strip(' .\n'))
                #print(response.documents[0]['type'])#.strip(' .\n'))
                nt_cleaned[len(nt_cleaned)] = tl
                return nt_cleaned
            
            else:
                nt_cleaned = False
                nt = list()
                for solr in self.solrs[1:]:
                    if len(nt) == 0:
                        response = self.search(url=solr,**query)
                        if response.status==200 and len(response.documents) > 0:
                            nt += response.documents[0]['ntriple'].split('.\n')[:-1]
                nt_cleaned = cleanResultSet(nt)
                tl = list()
                tl.append('<%s>' % resource)
                tl.append('<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>')
                tl.append(response.documents[0]['type'].strip(' .\n'))
                #print(response.documents[0]['type'])#.strip(' .\n'))
                nt_cleaned[len(nt_cleaned)] = tl
                return nt_cleaned
        except: 
            #self.logger.error('Could not fetch resource %s' % resource)
            return False  
                    
    def describeResource(self, resource):
        """Wrapper function to describe a resource given a URI either using INDEX lookup or via a SPARQL query"""
        label='<http://www.w3.org/2000/01/rdf-schema#label>'
        abstract='<http://dbpedia.org/ontology/abstract>'
        tp='<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'
        comment='<http://www.w3.org/2000/01/rdf-schema#comment>'
        seeAlso='<http://www.w3.org/2000/01/rdf-schema#seeAlso>'
        r = self.getResource(resource)
        response = dict()

        if r:
            properties = dict()
            [properties.update({triple[1]:triple[2]}) for triple in r.values()]
            #print (properties)
            if label in properties:
                
                if '@' in properties[label][-3:]:
                    response['label'] = properties[label][:-3]
                else:
                    response['label'] = properties[label]
                
            if abstract in properties:
                if '@' in properties[abstract][-3:]:
                    response['abstract'] = properties[abstract][:-3]
                else:
                    response['abstract'] = properties[abstract]
            if comment in properties:
                if '@' in properties[comment][-3:]:
                    response['comment'] =  properties[comment][:-3]
                else:
                    response['comment'] =  properties[comment]
                    
                if not abstract in properties:
                    response['abstract'] = response['comment']
                        
            if tp in properties:
                response['type'] = properties[tp]
            if seeAlso in properties:
                if not 'seeAlso' in response:
                    response['seeAlso'] = set()
                response['seeAlso'].add(properties[seeAlso])
            for prop in properties:
                if any([f in properties[prop].lower() for f in ['.png','.jpg','.gif']]):
                    if not 'img' in response:
                        response['img'] = set()
                    response['img'].add(properties[prop].strip('<>'))
        if not r or ('label' not in response and 'abstract' not in response and 'type' not in response):
            response = sparqlQueryByUri(resource)
            
        if 'label' in response and not 'type' in response:
            response['type'] = self.dbPediaIndexLookup(response['label'])['type']
        return response       

def sindiceMatch(value, kind):
    request = "http://api.sindice.com/v3/search?q={0}&fq=domain:dbpedia.org class:{1} format:RDF&format=json".format(value, kind)
    request = urllib.parse.quote(request, ':/=?<>"*&')
    logger.debug(request)
    #raw_output = urllib.request.urlopen(request).read()
    raw_output = requests.get(request)
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
    #raw_output = urllib.request.urlopen(request).read()
    raw_output = requests.get(request)
    output = ujson.loads(raw_output)
    link = list(output['entries'])[0]['link']
    return '<%(link)s>' % locals()

def sindiceFind2(prop, value, kind):
    return sindiceFind('*', prop, value, kind)

def sparqlQueryByUri(uri):
    """Find properties of a URI in the configured SPARQL endpoint and return label, abstract and type."""
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
    
def sparqlQueryByLabel(value, type=""):
    """Find a URI by label in the configured SPARQL endpoint and return it"""
    type_entry = ""
    if not type == "":
        types = mappings.get('enabled','types').strip(' ').split(',')
        if type in types:
            type_uri = mappings.get('mappings',type)
            type_entry = "?x rdf:type %s ." % type_uri
    
    if sparql:
        query = """
                PREFIX p: <http://dbpedia.org/property/>
                PREFIX dbpedia: <http://dbpedia.org/resource/>
                PREFIX category: <http://dbpedia.org/resource/Category:>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX dbo: <http://dbpedia.org/ontology/>
                SELECT ?x (count(distinct ?y) AS ?wikiPageWikiLinks) WHERE {
                  %(type_entry)s
                  ?x rdfs:label "%(value)s"@en .
                  ?x dbo:wikiPageWikiLink ?y
                } ORDER BY DESC(count(distinct ?y)) LIMIT 1
                """ % locals()
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

def cleanInversResultSet(resultSet, target):
    memory_store = rdflib.plugin.get('IOMemory', rdflib.graph.Store)()
    g=rdflib.Graph(memory_store)
    try:    
        g.parse(data=resultSet, format="nt")
        qres = g.query(
        """SELECT DISTINCT ?s ?p
           WHERE {
              ?s ?p <%s> .
           }""" % target)
        nt_cleaned = dict()
        i = 0
        for row in qres:
            triple = list()
            triple.append("<%s>" %str(row['s']))
            triple.append("<%s>" %str(row['p']))
            triple.append("<%s>" % target)
            nt_cleaned[i] = triple
            i += 1
    except:
        #print (sys.exc_info())
        #logger.warning('Parsing inverse failed for %s' % target)
        nt_cleaned = False
    return nt_cleaned

def cleanMultiResultSet(resultSet, targets):#
    resultSets = re.split(' .\n',resultSet)
    try:    
        nt_cleaned = dict()
        i = 0
        for row in resultSets[:-1]:
            triple = re.split(' ',row)
            if triple[2] in targets or triple[0] in targets:
                nt_cleaned[i] = triple
                i += 1
    except:
        #print (sys.exc_info())
        #logger.warning('Parsing inverse failed for %s' % target)
        nt_cleaned = False
    return nt_cleaned
        
def cleanInversResultSetFast(resultSet, target):
    resultSets = re.split(' .\n',resultSet)
    try:    
        nt_cleaned = dict()
        i = 0
        for row in resultSets[:-1]:
            triple = re.split(' ',row)
            if triple[2] == "<%s>" % target:
                nt_cleaned[i] = triple
                i += 1
    except:
        #print (sys.exc_info())
        #logger.warning('Parsing inverse failed for %s' % target)
        nt_cleaned = False
    return nt_cleaned        

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
    #print('done')
    return nt_cleaned  
    
def getResourceRemote(resource):
    """Fetch properties and children from a resource given a URI in the configured remote INDEX"""
    source = resource.strip('<>')
    request = 'http://api.sindice.com/v3/cache?pretty=true&url={0}'.format(source)
    try:
        #raw_output = urllib.request.urlopen(request).read()
        raw_output = requests.get(request)
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
        #raw_output = urllib.request.urlopen(request).read()
        raw_output = requests.get(request)
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

def addDirectedLink(source, target, predicate, inverse, resourcesByParent):
    if not target in resourcesByParent:
        resourcesByParent[target] = dict()
    link = dict()
    link['uri'] = predicate
    link['inverse'] = inverse
    resourcesByParent[target][source] = link

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

def chunks(l, n):
    return [l[i:i+n] for i in range(0, len(l), n)]

#print (sindiceMatch('David Guetta','person'))
#res = dbPediaLookup('David Guetta','')
#print (getResource(res))
#resourceretriever = Resourceretriever()
#print (resourceretriever.describeResource('http://dblp.l3s.de/d2r/resource/authors/Selver_Softic'))
#print (resourceretriever.getResource('http://dblp.l3s.de/d2r/resource/authors/Selver_Softic'))
#start = time.perf_counter()
#print(resourceretriever.getResourceLocal('http://dblp.l3s.de/d2r/resource/authors/Changqing_Li'))
#print (time.perf_counter() - start)
#print(resourceretriever.getResource('http://dbpedia.org/resource/Belgium'))
#print(resourceretriever.getResourceLocalInverse('http://dbpedia.org/resource/Elio_Di_Rupo'))
#bPediaLookup('Belgium')
#resourceretriever = Resourceretriever()
#print(resourceretriever.genUrls('http://dblp.l3s.de/d2r/resource/authors/Selver_Softic'))
#print(resourceretriever.genMultiUrls(['http://dblp.l3s.de/d2r/resource/authors/Selver_Softic','http://dbpedia.org/resource/Elio_Di_Rupo']))

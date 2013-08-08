import numpy as np
import ujson, urllib.request, urllib.parse, lxml.objectify, logging, sys, configparser, os, requests
from SPARQLWrapper import SPARQLWrapper, JSON
from core import config_search, utils
import graph_tool as gt

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
        
#print ("""
#.------..------.
#|G.--. ||T.--. |
#| :/\: || :/\: |
#| :\/: || (__) |
#| '--'G|| '--'T|
#`------'`------'""")
print ("EiCE GT plugin running on: %s :)" % sys.platform)

class Triple(object):
    pass

class Resourceretriever:
    
    def __init__(self, solrs=solrs):
        self.logger = logging.getLogger('pathFinder')
        self.config = config
        self.solrs = solrs
        self.auth = None
        self.session = requests.session()
    
    def genMultiUrls(self, resources):
        multi_urls = []
        #print (len(resources))
        resource_chunks = utils.chunks(list(resources), 8)
        rows = 25
        for resource_chunk in resource_chunks:
            queryParts = []
            invQueries = []
            for resource in resource_chunk:
                resource = resource.strip('<>!+&')
                resource = urllib.parse.quote(resource, ':\/=?<>"*')
                if not ('&' in resource or '#' in resource):
                    queryParts.append("<%s> * *" % (resource))
                    invQueries.append("* * <%s>&rows=%s" % (resource,rows))
            query = " OR ".join(queryParts)
            bases = []
            for solr in self.solrs:
                bases.append("%sselect?nq=%s&fl=id ntriple type&wt=json&qt=siren" % (solr,query))
                if not 'siren2' in solr:
                    for invQuery in invQueries:
                        bases.append("%sselect?nq=%s&fl=id ntriple type&wt=json&qt=siren" % (solr,invQuery))
            #for base in bases:
            #    print(len(base))
            multi_urls.append({'resources' : set(resource_chunk), 'urls' : bases})
        return multi_urls
    
    def processMultiResourceLocal(self, resources, resp):
        """Process subjects and predicate linking to a given URI, the URI as object in the configured local INDEX"""
        #print (resp)
        try:
            if len(resp['docs']) > 0:
                nt = ""
                for document in resp['docs']:
                    nt += document['ntriple']
                nt_cleaned = utils.cleanMultiResultSet(nt,resources)
                return nt_cleaned
            
            else:
                return False
        except: 
            #self.logger.error('Could not fetch resource inverse %s' % resource)
            return False
    
    def processMultiResource(self, res, rp, resourcesByParent, additionalResources, blacklist, inverse = False):
        resources = res
        try:
            resp = ujson.decode(rp.content)['response']
            newResources = []
            results = False
            newResources = self.processMultiResourceLocal(resources, resp)
            if newResources:
                results = dict()
                for tripleKey, triple in newResources.items():
                    result = Triple()
                    if triple[0] in resources:
                        result.source = triple[0]
                        result.targetRes = triple[2]
                        result.inverse = True
                    else:
                        result.targetRes = triple[0]
                        result.source = triple[2]
                        result.inverse = False
                    result.predicate = triple[1]
                    if not result.source in results:
                        results[result.source] = set()
                    if utils.isResource(result.targetRes) and (result.predicate not in blacklist) and result.targetRes.startswith('<') and result.targetRes.endswith('>') and any(domain in result.targetRes for domain in config_search.valid_domains): #and 'dbpedia' in targetRes:
                        results[result.source].add(result)
                        
                for resource in results:
                    if not resource in additionalResources:
                        additionalResources[resource] = set()
                    additionalResources[resource] = additionalResources[resource].union(results[resource])
        except:
            logger.error('error in retrieving %s' % resources)
            logger.error(sys.exc_info())
        
    def jaccard(self,nodeA,nodeB):
        respbA = set()
        respbB = set()
        for link in nodeA:
            if link:
                respbA.add(link.predicate)
            
        for link in nodeB:
            if link:
                respbB.add(link.predicate)
                
        """Computes the jaccard between two nodes."""
        return 1- ( len(respbA & respbB) / len(respbA | respbB) )
       
    def expandResource(self, resource):
        results = set()
        newResources = self.getResource(resource)
        if newResources:
            for tripleKey, triple in newResources.items():
                result = Triple()
                if resource == triple[0]:
                    result.source = triple[0]
                    result.targetRes = triple[2]
                    result.inverse = True
                else:
                    result.targetRes = triple[0]
                    result.source = triple[2]
                    result.inverse = False
                result.predicate = triple[1]
                if utils.isResource(result.targetRes) and (result.predicate not in config_search.blacklist) and result.targetRes.startswith('<') and result.targetRes.endswith('>') and any(domain in result.targetRes for domain in config_search.valid_domains): #and 'dbpedia' in targetRes:
                    results.add(result)
        return results
         
    def fetchResource(self, resource, additionalResources, blacklist):   
        results = self.expandResource(resource)
        
        if results:
            if not resource in additionalResources:
                        additionalResources[resource] = set()
            additionalResources[resource] = additionalResources[resource].union(results)

#print (sindiceMatch('David Guetta','person'))
#res = dbPediaLookup('David Guetta','')
#print (getResource(res))
#resourceretriever = Resourceretriever()
#print (resourceretriever.describeResource('http://dbpedia.org/resource/Belgium'))
#print (resourceretriever.describeResource('http://dblp.l3s.de/d2r/resource/authors/Selver_Softic'))
#print(resourceretriever.getResource('http://dblp.l3s.de/d2r/resource/authors/Changqing_Li'))
#print(resourceretriever.getResource('http://dblp.l3s.de/d2r/resource/authors/Tok_Wang_Ling'))
#print(resourceretriever.getResourceLocalInverse('http://dbpedia.org/resource/Elio_Di_Rupo'))
#bPediaLookup('Belgium')

import numpy as np
import rdflib, requests, ujson, urllib
logger = logging.getLogger('pathFinder')

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

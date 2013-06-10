'''
Created on 17-sep.-2012

@author: ldevocht
'''
import urllib.request
import urllib.parse
import lxml.objectify
import logging
import configparser
import os
from core import resourceretriever
from mysolr import Solr

config = resourceretriever.config
mapping = resourceretriever.mappings
logger = logging.getLogger('pathFinder')


def dbPediaPrefix(prefix):
    server = config.get('services', 'lookup')
    gateway = '{0}/api/search.asmx/PrefixSearch?MaxHits=12&QueryString={1}'.format(server,prefix)
    request = urllib.parse.quote(gateway, ':/=?<>"*&')
    logger.debug('Request %s' % request)
    raw_output = urllib.request.urlopen(request).read()
    root = lxml.objectify.fromstring(raw_output)
    results = list()
    if hasattr(root, 'Result'):
        for result in root.Result:
            if prefix.lower() in result.Label[0].text.lower() and hasattr(result.Classes, 'Class'):
                klasses = result.Classes.Class
                if hasattr(klasses, 'Label'):
                    klasse = klasses
                else:
                    klasse = klasses[0]
                item = dict()
                item['label'] = result.Label[0].text
                item['category']=klasse.Label.text.capitalize()
                item['uri']=result.URI[0].text
                local_hits = resourceretriever.getResourceLocal(item['uri'].strip("<>"))
                n_hits = 0
                if local_hits:
                    for triple in local_hits:
                        if local_hits[triple][1] not in resourceretriever.blacklist:
                            n_hits += 1
                    if n_hits > 8:
                        results.append(item)

    return results

def prefix(prefix):
    results = list()

    results += dbPediaPrefix(prefix)
        
    if config.has_option('services','lookup_index'):
        lookup_server = config.get('services', 'lookup_index')
        lookup_solr = Solr(lookup_server)
        query={'q':'lookup:{0}*'.format(prefix.lower()),'fl':'url label type','timeAllowed':'5000'}
        response = lookup_solr.search(**query)
    
        if response.status==200 and len(response.documents) > 0:
            for doc in response.documents:
                item = dict()
                item['category']=doc['type'].split(' ')[0].rsplit('/')[-1].rsplit('#')[-1].strip('<>".')
                item['uri']=doc['url']
                item['label']=doc['label'].split('.')[0].split('"^^')[0].strip('<>".')
                results.append(item)
                
    return results
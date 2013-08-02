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
from core.resourceretriever import Resourceretriever
from core import resourceretriever
import time
import re
import ujson
import requests

config = resourceretriever.config
mapping = resourceretriever.mappings
logger = logging.getLogger('pathFinder')
lookup_server = config.get('services', 'lookup_index')
#lookup_solr = Solr(lookup_server)

class TypeAhead:        
    def dbPediaPrefix(self, prefix):
        server = config.get('services', 'lookup')
        gateway = '{0}/api/search.asmx/PrefixSearch?MaxHits=7&QueryString={1}'.format(server,prefix)
        requestUrl = urllib.parse.quote(gateway, ':/=?<>"*&')
        logger.debug('Request %s' % requestUrl)
        #rq = grequests.get(requestUrl)
        #response = grequests.map([rq])
        #raw_output = response[0].content
        raw_output = urllib.request.urlopen(requestUrl,timeout=2).read()
        #s = requests.Session()
        #s.headers.update({'Connection': 'close'})
        #r = s.get(requestUrl)
        #(s.headers)
        #print(r.headers)
        #raw_output = r.content
        root = lxml.objectify.fromstring(raw_output)
        results = list()
        if hasattr(root, 'Result'):
            logger.debug('Found %s results' % len(root.Result))
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
                    logger.debug('Fetching local hits for %s' % len(item['uri']))
                    local_hits = Resourceretriever().getResource(item['uri'].strip("<>"),False)
                    if local_hits:
                        logger.debug('Found %s hits' % len(local_hits))
                    n_hits = 0
                    if local_hits:
                        for triple in local_hits:
                            if local_hits[triple][1] not in resourceretriever.blacklist:
                                n_hits += 1
                        if n_hits > 8:
                            results.append(item)
        else:
            logger.debug('Found nothing for prefix %s' % prefix)
    
        return results
    
    def prefix(self, prefix,lookup_server=lookup_server):
        results = list()
        if len(prefix) > 2:
            logger.debug('looking up %s on dbpedia lookup' % prefix)
            results += self.dbPediaPrefix(prefix)
            logger.debug('looking up %s on local index' % prefix)
            if config.has_option('services','lookup_index'):
                #query={'q':'lookup:"{0}*"'.format(re.escape(prefix).lower()),'fl':'url label type','timeAllowed':'100','rows':'7'}
                #response = lookup_solr.search(**query)
                query = '%sselect?q=lookup:"%s*"&fl=url label type&wt=json' % (lookup_server,re.escape(prefix).lower())
                rsp = requests.get(query)
                #response = grequests.map([rq])
                response = ujson.decode(rsp.content)['response']
                if len(response['docs']) > 0:
                    for doc in response['docs']:
                        item = dict()
                        item['category']=doc['type'].split(' ')[0].rsplit('/')[-1].rsplit('#')[-1].strip('<>".')
                        if item['category'] == 'Agent':
                            item['category'] = 'Author'
                        item['uri']=doc['url']
                        item['label']=(doc['label'].split('.')[0].split('"^^')[0]).strip('\" <>.')
                        results.append(item)
            logger.debug('done finding matches for %s' % prefix)
                    
        return results

#print(TypeAhead().prefix('Selver'))
#print(TypeAhead().dbPediaPrefix('Selver'))
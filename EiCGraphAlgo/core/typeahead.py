'''
Created on 17-sep.-2012

@author: ldevocht
'''
import urllib.request
import urllib.parse
import lxml.objectify
import requests
import logging
import configparser
import os
from core.resourceretriever import Resourceretriever
from core import resourceretriever
from mysolr import Solr
import requests
import time
import re

config = resourceretriever.config
mapping = resourceretriever.mappings
logger = logging.getLogger('pathFinder')

class TypeAhead:
    def __init__(self):
        lookup_server = config.get('services', 'lookup_index')
        self.lookup_solr = Solr(lookup_server)
        
    def dbPediaPrefix(self, prefix):
        server = config.get('services', 'lookup')
        gateway = '{0}/api/search.asmx/PrefixSearch?MaxHits=7&QueryString={1}'.format(server,prefix)
        requestUrl = urllib.parse.quote(gateway, ':/=?<>"*&')
        logger.debug('Request %s' % requestUrl)
        #raw_output = urllib.request.urlopen(requestUrl,timeout=2).read()
        r = requests.get(requestUrl)
        raw_output = r.content
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
                    local_hits = Resourceretriever().getResourceLocal(item['uri'].strip("<>"))
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
    
    def prefix(self, prefix):
        results = list()
        if len(prefix) > 2:
            logger.debug('looking up %s on dbpedia lookup' % prefix)
            results += self.dbPediaPrefix(prefix)
            logger.debug('looking up %s on local index' % prefix)
            if config.has_option('services','lookup_index'):
                query={'q':'lookup:"{0}*"'.format(re.escape(prefix).lower()),'fl':'url label type','timeAllowed':'100','rows':'7'}
                response = self.lookup_solr.search(**query)
                if response.status==200 and len(response.documents) > 0:
                    for doc in response.documents:
                        item = dict()
                        item['category']=doc['type'].split(' ')[0].rsplit('/')[-1].rsplit('#')[-1].strip('<>".')
                        if item['category'] == 'Agent':
                            item['category'] = 'Author'
                        item['uri']=doc['url']
                        item['label']=(doc['label'].split('.')[0].split('"^^')[0]).strip('\" <>.')
                        results.append(item)
            logger.debug('done finding matches for %s' % prefix)
                    
        return results
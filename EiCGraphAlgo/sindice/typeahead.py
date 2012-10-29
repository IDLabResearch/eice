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
from sindice import resourceretriever

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__))+'/config.ini') 
logger = logging.getLogger('pathFinder')

def dbPediaPrefix(prefix):
    server = config.get('services', 'lookup')
    gateway = '{0}/api/search.asmx/PrefixSearch?QueryString={1}'.format(server,prefix)
    request = urllib.parse.quote(gateway, ':/=?<>"*&')
    logger.debug('Request %s' % request)
    raw_output = urllib.request.urlopen(request).read()
    root = lxml.objectify.fromstring(raw_output)
    results = list()
    for result in root.Result:
        if hasattr(result.Classes, 'Class'):
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
            if len(local_hits > 0):
                results.append(item)

    return results

#print (dbPediaPrefix("den"))

'''
Created on 17-sep.-2012

@author: ldevocht
'''
import urllib.request
import urllib.parse
import lxml.objectify
import logging

logger = logging.getLogger('pathFinder')

def dbPediaPrefix(prefix):
    gateway = 'http://lookup.dbpedia.org/api/search.asmx/PrefixSearch?QueryString={0}'.format(prefix)
    request = urllib.parse.quote(gateway, ':/=?<>"*&')
    logger.debug('Request '+request)
    raw_output = urllib.request.urlopen(request).read()
    root = lxml.objectify.fromstring(raw_output)
    results = dict()
    for result in root.Result:
        if hasattr(result.Classes, 'Class'):
            klasses = result.Classes.Class
            if hasattr(klasses, 'Label'):
                klasse = klasses
            else:
                klasse = klasses[0]
            results[result.Label[0].text] = dict()
            results[result.Label[0].text]['type']=klasse.Label.text
            results[result.Label[0].text]['uri']=result.URI[0].text
        else:
            results[result.Label[0].text] = ""
    return results
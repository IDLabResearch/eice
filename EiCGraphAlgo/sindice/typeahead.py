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
            item['type']=klasse.Label.text
            item['value']=result.URI[0].text
            results.append(item)

    return results

print (dbPediaPrefix('Lon'))
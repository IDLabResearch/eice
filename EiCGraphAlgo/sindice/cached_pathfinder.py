import pickle

import os, os.path, sys

class CachedPathFinder:
    paths = dict()
    
    def __init__(self):
        path = os.path.dirname(os.path.abspath(sys.modules[CachedPathFinder.__module__].__file__))

        for root, dirs, files in os.walk('{0}/cached_paths'.format(path)):
            print (root)
            for f in files:
                dump = pickle.load(open('{0}/{1}'.format(root,f),'rb'))
                self.paths[dump['destination']] = dump
                
    def getPaths(self, destination):
        return self.paths[destination]
    
#cpf = CachedPathFinder()

#print (cpf.getPaths('http://dbpedia.org/resource/France'))
from sindice import search,randompath
import pickle
import ujson
import numpy as np
                
def generateCachedPaths():
    for s in randompath.sources:
        for d in randompath.destinations:
            print ("Calculation for {0} to {1}".format(s,d)) 
            r = dict()
            try:
                r = search.search(s,d)
                r['source'] =  s
                r['destination'] = d
                print("Execution time: %s" % str(r['execution_time']))
                pickle.dump(r,open( "cached_paths/%s.dump" % hash('{0}_{1}'.format(s,d)), "wb" ))
            except:
                print("Could not find path between {0} and {1}".format(s,d))
#generateCachedPaths()
            
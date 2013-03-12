from core import search,randompath
import pickle
import ujson, os, inspect, time, gc, sys
import logging.config
import numpy as np
import timeit
import math

logging.config.fileConfig('logging.conf')
 
def generateCachedPaths():
    root = (os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))
    start_time = time.time()
    n = 0
    total = len(randompath.sources)*len(randompath.destinations)
    for s in randompath.sources:
        for d in randompath.destinations:
            print ("Calculation for {0} to {1}".format(s,d)) 
            r = dict()
            try:
                r = search.search(s,d)
                r['source'] =  s
                r['destination'] = d
                print("Execution time: %s" % str(r['execution_time']))
                pickle.dump(r,open( "core/cached_paths/%s.dump" % hash('{0}_{1}'.format(s,d)), "wb" ))
            except:
                print("Could not find path between {0} and {1}".format(s,d))
                print(sys.exc_info())
            gc.collect()
            elapsed_time = time.time() - start_time
            n += 1
            remaining_time = elapsed_time * total / n - elapsed_time
            print("{0} of {3} Elapsed: {1} ETR: {2}".format(n,elapsed_time,remaining_time,total))

generateCachedPaths()


from sindice import cached_pathfinder
import scipy.stats as spst
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import sys, time

def plot():
    plt.clf()
    cpf = cached_pathfinder.CachedPathFinder()
    total_paths = cpf.loadStoredPaths(max=None)
    #print (total_paths)
    #print (cpf.path_execution_times)
    flattened_checked_resources = list()
    for x in cpf.path_cached_resources:
        for t in cpf.path_cached_resources[x]:
            flattened_checked_resources.append(t)
    
    #print (flattened_checked_resources)
    
    # Set the title.
    plt.title('Distribution of checked resources (n = %s)' % total_paths,fontsize=12)
    
    # Set the X Axis label.
    plt.xlabel('(#)',fontsize=9)
    
    # Set the Y Axis label.
    plt.ylabel('(#)',fontsize=9)
    #plt.yscale('log')
    
    plt.hist(flattened_checked_resources,bins=10, range=None, normed=False,alpha=0.5)
    
    try:
        path = "/tmp/checked_resources_{0}_{1}.png".format(hash(time.time()),np.random.randint(10000))
        plt.savefig(path)
    except:
        print (sys.exc_info())
    return path
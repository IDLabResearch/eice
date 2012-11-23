from sindice import cached_pathfinder
import scipy.stats as spst
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import sys, time

def plot(cpf = cached_pathfinder.CachedPathFinder()):
    plt.clf()
    total_paths = cpf.loadStoredPaths(max=None)
    #print (total_paths)
    #print (cpf.path_execution_times)
    flattened_execution_times = list()
    for x in cpf.path_execution_times:
        for t in cpf.path_execution_times[x]:
            flattened_execution_times.append(t)
    
    #print (flattened_execution_times)
    
    # Set the title.
    plt.title('Distribution of execution times (n = %s)' % total_paths,fontsize=12)
    
    # Set the X Axis label.
    plt.xlabel('(ms)',fontsize=9)
    plt.xticks(np.arange(0,np.max(flattened_execution_times),4000))
    
    # Set the Y Axis label.
    plt.ylabel('(fraction)',fontsize=9)
    #plt.yscale('log')
    bins = np.int(np.max(flattened_execution_times) / 2000) + 1
    plt.hist(flattened_execution_times, bins = bins, range=[0,np.max(flattened_execution_times)], normed=True,alpha=0.5, cumulative=True)
    
    try:
        path = "/tmp/analysis_et_{0}_{1}.png".format(hash(time.time()),np.random.randint(10000))
        plt.savefig(path)
    except:
        print (sys.exc_info())
    return path
from core import cached_pathfinder
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
    plt.xlabel('Execution time(ms)',fontsize=9)
    #plt.xscale('log')
    #plt.xlim(10000,250000)
    plt.xticks(np.arange(0,np.max(flattened_execution_times),30000))
    
    # Set the Y Axis label.
    plt.ylabel('Occurence (fraction)',fontsize=9)
    #plt.yscale('log')
    plt.ylim(0.2,1)
    bins = np.int(np.max(flattened_execution_times) / 7500) + 1
    plt.hist(flattened_execution_times, bins = bins, range=[0,np.max(flattened_execution_times)], normed=True,alpha=0.5, cumulative=True)
    
    try:
        path = "/tmp/analysis_et_{0}_{1}.png".format(hash(time.time()),np.random.randint(10000))
        plt.savefig(path)
    except:
        #print (sys.exc_info())
        pass
    return path

#print(plot())
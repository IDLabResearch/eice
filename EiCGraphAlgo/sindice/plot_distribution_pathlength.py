from sindice import cached_pathfinder
import scipy.stats as spst
import scipy.stats as ss
import scipy as sp
from scipy.stats import ks_2samp
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import sys, time

def plot(cpf = cached_pathfinder.CachedPathFinder()):
    plt.clf()
    total_paths = cpf.loadStoredPaths(max=None)
    #print (total_paths)
    #print (cpf.path_lengths)
    flattened_lengths = list()
    cpf.path_lengths.pop(len(cpf.path_lengths))
    for x in cpf.path_lengths:
        i = 0
        for i in range(cpf.path_lengths[x]):
            flattened_lengths.append(x)
            i += 1
            
    y = list(cpf.path_lengths.values())
    x = list(cpf.path_lengths.keys())
    
    y_n = list()
    for el in y:
        y_n.append(np.divide(el,total_paths))
    x_n = list()
    for x_el in x:
        x_n.append(x_el - 0.4)
        
    #variation = spst.tstd(flattened_lengths)
    #median = spst.tmean(flattened_lengths)
    mean = np.average(np.array(flattened_lengths))
    #print (x_n)
    #print (y_n)
    #print (median)
    #print (variation)
    print ("mean = %s " % mean )
    l = np.linspace(0,np.max(np.array(x)),np.max(np.array(y)))
    # Set the title.
    plt.title('Distribution of path length (n = %s)' % total_paths,fontsize=12)
    
    # Set the X Axis label.
    plt.xlabel('(steps)',fontsize=9)
    plt.xlim(0,np.max(x)+1)
    x_r = np.arange(np.max(x)+1,step = 0.1)
    # Set the Y Axis label.
    plt.ylabel('(fraction)',fontsize=9)
    fit_alpha,fit_loc,fit_beta=ss.gamma.fit(flattened_lengths)
    print(fit_alpha,fit_loc,fit_beta)
    print(fit_alpha * fit_beta)
    fit_gamma = ss.gamma.rvs(fit_alpha,loc=fit_loc,scale=fit_beta, size=len(flattened_lengths))
    print (fit_gamma)
    print (ks_2samp(flattened_lengths, fit_gamma))
    
    plt.bar(x_n,y_n,alpha=0.5)
    #plt.plot(l,mlab.normpdf(l,median,np.sqrt(variation)),color='tomato')
    dist = ss.gamma(fit_alpha,loc=fit_loc,scale=fit_beta)
    plt.plot(x_r, dist.pdf(x_r), ls='-', c='tomato')
    #test http://docs.scipy.org/doc/scipy/reference/tutorial/stats.html look for test
    
    try:
        path = "/tmp/analysis_{0}_{1}.png".format(hash(time.time()),np.random.randint(10000))
        plt.savefig(path)
    except:
        print (sys.exc_info())
    return path
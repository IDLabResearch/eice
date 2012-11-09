from sindice import cached_pathfinder
import scipy.stats as spst
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import sys, time


plt.clf()

cpf = cached_pathfinder.CachedPathFinder()
total_paths = cpf.loadStoredPaths(max=None)
print (total_paths)
print (cpf.path_lengths)
flattened_lengths = list()
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
variation = spst.tstd(flattened_lengths)
median = spst.tmean(flattened_lengths)
print (x)
print (y_n)
print (median)
print (variation)
l = np.linspace(0,np.max(np.array(x)),np.max(np.array(y)))
plt.bar(x,y_n)
plt.plot(l,mlab.normpdf(l,median,np.sqrt(variation)),color='r')

try:
    path = "/tmp/analysis_{0}_{1}.png".format(hash(time.time()),np.random.randint(10000))
    plt.savefig(path)
except:
    print (sys.exc_info())
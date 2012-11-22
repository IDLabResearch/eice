from sindice import cached_pathfinder
import scipy.stats as spst
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import sys, time
from pylab import *

def plot():
    plt.clf()
    
    cpf = cached_pathfinder.CachedPathFinder()
    hitrate = cpf.hitrate()

    
    # make a square figure and axes
    plt.figure(1, figsize=(6,6))
    plt.axes([0.1, 0.1, 0.8, 0.8])
    
    # The slices will be ordered and plotted counter-clockwise.
    misses = hitrate['total'] - hitrate['found']
    labels = 'Hits (%s)' % hitrate['found'], 'Misses (%s)' %misses 
    fracs = [hitrate['found'], misses]
    explode=( 0, 0.05 )
    
    plt.pie(fracs, explode=explode, labels=labels,  colors=('lawngreen', 'tomato'),
                    autopct='%1.1f%%', shadow=True, startangle=90)
                    # The default startangle is 0, which would start
                    # the Frogs slice on the x-axis.  With startangle=90,
                    # everything is rotated counter-clockwise by 90 degrees,
                    # so the plotting starts on the positive y-axis.
    
    plt.title('Pathfinding Hitrate', bbox={'facecolor':'0.8', 'pad':5})
    
    try:
        path = "/tmp/hitrate_{0}_{1}.png".format(hash(time.time()),np.random.randint(10000))
        plt.savefig(path)
    except:
        print (sys.exc_info())
    return path
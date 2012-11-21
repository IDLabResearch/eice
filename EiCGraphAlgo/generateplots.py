from sindice import plot_distribution_execution_times
from sindice import plot_distribution_pathlength
from sindice import plot_hitrate
from sindice import plot_time_vs_pathlengths
import inspect, os
import shutil

print ('Done generating plots. They are located in /tmp')

def generatePlots():
    plots = set()
    plots.add(plot_distribution_execution_times.plot())
    plots.add(plot_distribution_pathlength.plot())
    plots.add(plot_hitrate.plot())
    plots.add(plot_time_vs_pathlengths.plot())
    
    root = (os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))
    
    i=0
    for plot in plots:
        i+=1
        shutil.copyfile(plot, "{0}/static/imgs/plots{1}.png".format(root,i))
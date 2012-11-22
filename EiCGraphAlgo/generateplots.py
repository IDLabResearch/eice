from sindice import plot_distribution_execution_times
from sindice import plot_distribution_checked_resources
from sindice import plot_checked_resources_vs_execution_times
from sindice import plot_checked_resources_vs_pathlengths
from sindice import plot_distribution_pathlength
from sindice import plot_hitrate
from sindice import plot_time_vs_pathlengths

import inspect, os
import shutil, logging

logger = logging.getLogger('root')

def generatePlots():
    plots = list()
    plots.append(plot_hitrate.plot())
    plots.append(plot_distribution_execution_times.plot())
    plots.append(plot_distribution_pathlength.plot())
    plots.append(plot_time_vs_pathlengths.plot())
    plots.append(plot_distribution_checked_resources.plot())
    plots.append(plot_checked_resources_vs_pathlengths.plot())
    plots.append(plot_checked_resources_vs_execution_times.plot())
    
    root = (os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))
    
    i=0
    for plot in plots:
        i+=1
        shutil.copyfile(plot, "{0}/static/imgs/plots{1}.png".format(root,i))
        
    logging.info('Done generating plots. They are located in /tmp and %s/static/imgs' %root)

generatePlots()
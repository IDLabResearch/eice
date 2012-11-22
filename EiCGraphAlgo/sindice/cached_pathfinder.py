import pickle
import numpy as np
import networkx as nx
import time
import os, os.path, sys, logging
from sindice import graph, resourceretriever, randompathgenerator
import matplotlib.pyplot as plt
import glob

logger = logging.getLogger('pathFinder')

class CachedPathFinder:

    def __init__(self):
        logger.debug('init CPF')
        self.paths = False
        self.resources = dict()
        self.resources_counts = dict()
        self.resources_by_parent = dict()
        self.properties = dict()
        self.properties_counts = dict()
        self.properties_by_parent = dict()
        self.stateGraph = False
        self.loaded = False
        self.path_lengths = dict()
        self.path_execution_times = dict()
        self.path_cached_resources = dict()
        self.path_execution_time_by_checked_resources = dict()
        self.path = os.path.dirname(os.path.abspath(sys.modules[CachedPathFinder.__module__].__file__))
        
    def loadCachedPaths(self):
        for root, dirs, files in os.walk('{0}/cached_paths'.format(self.path)):
            #print (root)
            for f in files:
                dump = pickle.load(open('{0}/{1}'.format(root,f),'rb'))
                if not dump['destination'] in self.paths:
                    self.paths[dump['destination']] = dict()
                self.paths[dump['destination']][dump['source']] = dump
                
    def getPaths(self, destination, source):
        if not self.paths:
            self.paths = dict()
            self.loadCachedPaths()
            
        if destination in self.paths and source in self.paths[destination]:
            return self.paths[destination][source]
        else:
            return False
        
    def hitrate(self):
        n = 0
        found = 0
        path="{0}/../query.log*".format(self.path)
        for file in glob.glob(path):
            with open(file,'rb') as f:
                prev = None
                for line in f:
                    n+=1
                    current = line[41]
                    if current == 123:
                        found += 1
        return {'found':found,'total':np.int(n/2)+1}
            
    def loadStoredPaths(self, blacklist=set(), max=150):
        root = '{0}/stored_paths'.format(self.path)
        for root, dirs, files in os.walk(root):
            files = [os.path.join(root, f) for f in files] # add path to each file
            files.sort(key=lambda x: os.path.getmtime(x),reverse=True)
        
        files_to_load = files[0:max]    
        for f in files_to_load:
            dump = pickle.load(open(f,'rb'))
            
            if 'paths' in dump:
                for path in dump['paths']:
                    length = len(path['edges'])
                    if length in self.path_lengths:
                        self.path_lengths[length] += 1
                    else:
                        self.path_lengths[length] = 1
                        
                    if length in self.path_execution_times:
                        self.path_execution_times[length].append(dump['execution_time'])
                    else:
                        self.path_execution_times[length] = list()
                        self.path_execution_times[length].append(dump['execution_time'])
                        
                    if 'checked_resources' in dump:
                        if dump['checked_resources'] in self.path_execution_time_by_checked_resources:
                            self.path_execution_time_by_checked_resources[dump['checked_resources']].append(dump['execution_time'])
                        else:
                            self.path_execution_time_by_checked_resources[dump['checked_resources']] = list()
                            self.path_execution_time_by_checked_resources[dump['checked_resources']].append(dump['execution_time'])
                        
                        if length in self.path_cached_resources:
                            self.path_cached_resources[length].append(dump['checked_resources'])
                        else:
                            self.path_cached_resources[length] = list()
                            self.path_cached_resources[length].append(dump['checked_resources'])
                    
                    for edge in path['edges']:
                        if edge in self.properties_counts:
                            self.properties_counts[edge] += 1
                        else:
                            self.properties_counts[edge] = 1
                            self.properties[len(self.properties)] = edge
                    
                    for iterator in graph.rolling_window(path['edges'], 2):
                        i = 0
                        steps = list(iterator)
                        if len(steps) == 2:
                            resourceretriever.addDirectedLink(steps[0], steps[1],  [path['vertices'][i],path['vertices'][i+1]], True, self.properties_by_parent)
                            resourceretriever.addDirectedLink(steps[1], steps[0], [path['vertices'][i],path['vertices'][i+1]], False, self.properties_by_parent)
                            i += 1
                        
                    for vertex in path['vertices']:
                        if vertex in self.resources_counts:
                            self.resources_counts[vertex] += 1
                        else:
                            self.resources_counts[vertex] = 1
                            self.resources[len(self.resources)] = vertex
                    
                    for iterator in graph.rolling_window(path['vertices'], 2):
                        i = 0
                        steps = list(iterator)
                        if len(steps) == 2:
                            resourceretriever.addDirectedLink(steps[0], steps[1], path['edges'][i], True, self.resources_by_parent)
                            resourceretriever.addDirectedLink(steps[1], steps[0], path['edges'][i], False, self.resources_by_parent)
                            i += 1
        self.loaded = True
        return len(files_to_load)
    
    def getStoredPath(self, hash):
        root = '{0}/stored_paths'.format(self.path)
        f = os.path.join(root, '%s.dump' % hash)
        try:    
            dump = pickle.load(open(f,'rb'))
            dump.pop('paths')
            #print (dump.pop('checked_resources'))
            return dump
        except:
            return False      
    
    def getNodeData(self, blacklist=set()):
        if not self.loaded:
            self.loadStoredPaths(blacklist)
        node_data = dict()
        nodes = list()
        links = list()
        loaded = set()
        
        res = list(sorted(self.resources_counts, key=self.resources_counts.__getitem__, reverse=True))
        important = frozenset(res[:250])
        
        for resource in self.resources:
            if self.resources[resource] in important:
                node = dict()
                label = self.resources[resource].strip('<>')
                splitted = label.split("/")
                final_label = splitted[len(splitted)-1]
                node['match'] = 1
                node['name'] = final_label
                node['artist'] = resourceretriever.dbPediaIndexLookup(final_label)['type']
                node['id'] = "id%s" % hash(label)
                loaded.add(label)
                node['playcount'] = self.resources_counts[self.resources[resource]]
                nodes.append(node)
        
        for resource in self.resources_by_parent:
            for parent in self.resources_by_parent[resource]:
                if resource in loaded and parent in loaded:
                    link = dict()
                    link['source'] = "id%s" % hash(resource)
                    link['target'] = "id%s" % hash(parent)
                    links.append(link)
        
        node_data['nodes'] = nodes
        node_data['links'] = links
        return node_data
    
    def buildMatrix(self, blacklist=set()):
        if not self.loaded:
            self.loadStoredPaths(blacklist)
        n = len(self.resources)      
        #print(n)
        self.stateGraph = np.zeros((n, n), np.byte)
        [self.buildGraph(i, n) for i in range(n)]
        #print (self.stateGraph)
        return self.stateGraph
        
    def dice(self,nodeA,nodeB):
        resA = frozenset(self.resources_by_parent[self.resources[nodeA]])
        resB = frozenset(self.resources_by_parent[self.resources[nodeB]])
        return len(resA & resB)       
    
    def buildGraph(self, i, n):
        row = np.zeros(n, np.byte)
        [self.matchResource(i, j, row) for j in range(n)]
        self.stateGraph[i] = row
        
    def matchResource(self, i, j, row):
        try:
            if i == j:
                row[j] = 1
            elif not self.resources[j] in self.resources_by_parent:
                row[j] = 0
            elif self.resources[i] in self.resources_by_parent[self.resources[j]]:
                row[j] = 1
            else:
                row[j] = 0
        except:
            logger.error ('error %s' % str(j))
            logger.error (self.resources)
            quit()
    
    def getGraph(self):
        return self.stateGraph
    
    def getResources(self):
        return self.resources
    
    def getResourcesByParent(self):
        return self.resources_by_parent
    
    def visualize(self, path=None):
        plt.clf()  
        G = graph.buildWeightedGraph(self)
        pos=nx.spring_layout(G)
        offset = 0.06
        pos_labels = {}
        keys = pos.keys()
        for key in keys:
            x, y = pos[key]
            pos_labels[key] = (x, y-offset)
                        
        labels=dict()
        widths = []
        edge_labels=dict()
             
        for node in self.getResources():
                labels[node] = self.getResources()[node]
                widths.append(self.resources_counts[self.getResources()[node]])
        
        nx.draw_networkx_edges(G, pos, width=1,alpha=1)        
        nx.draw_networkx_edges(G, pos, width=widths,alpha=0.5)
        nx.draw_networkx_nodes(G, pos, size=1,node_color='b',alpha=0.7)
        
        nx.draw_networkx_labels(G,pos_labels,labels,font_size=6)
        nx.draw_networkx_edge_labels(G,pos,edge_labels=edge_labels,font_size=6)
        #logger.debug(G.nodes)
        plt.axis('off')
        
        try:
            path = "/tmp/analysis_{0}_{1}.png".format(hash(time.time()),np.random.randint(10000))
            plt.savefig(path)
        except:
            print (sys.exc_info())
            
        return path
                            
#cpf = CachedPathFinder()
#r = randompathgenerator.randomSourceAndDestination()
#cpf.getPaths(r['destination'], r['source'])
#cpf.buildMatrix()
#cpf.visualize()
#print (cpf.getStoredPath('h-4358414122171955722'))
#print (cpf.getPaths('http://dbpedia.org/resource/France'))

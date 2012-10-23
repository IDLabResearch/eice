import pickle
import numpy as np
import networkx as nx
import time
import os, os.path, sys, logging
from sindice import graph, resourceretriever
import matplotlib.pyplot as plt

logger = logging.getLogger('pathFinder')

class CachedPathFinder:

    def __init__(self):
        logger.debug('init CPF')
        self.paths = dict()
        self.resources = dict()
        self.resources_counts = dict()
        self.resources_by_parent = dict()
        self.properties = dict()
        self.properties_counts = dict()
        self.properties_by_parent = dict()
        self.stateGraph = False
        self.path = os.path.dirname(os.path.abspath(sys.modules[CachedPathFinder.__module__].__file__))
        for root, dirs, files in os.walk('{0}/cached_paths'.format(self.path)):
            print (root)
            for f in files:
                dump = pickle.load(open('{0}/{1}'.format(root,f),'rb'))
                self.paths[dump['destination']] = dump
                
    def getPaths(self, destination):
        return self.paths[destination]
    
    def buildMatrix(self, blacklist=set()):
        for root, dirs, files in os.walk('{0}/stored_paths'.format(self.path)):
            print (root)
            for f in files:
                dump = pickle.load(open('{0}/{1}'.format(root,f),'rb'))
                if 'paths' in dump:
                    for path in dump['paths']:
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
                                resourceretriever.addDirectedLink(steps[0], steps[1], [path['vertices'][i],path['vertices'][i+1]], self.properties_by_parent)
                                resourceretriever.addDirectedLink(steps[1], steps[0], [path['vertices'][i],path['vertices'][i+1]], self.properties_by_parent)
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
                                resourceretriever.addDirectedLink(steps[0], steps[1], path['edges'][i], self.resources_by_parent)
                                resourceretriever.addDirectedLink(steps[1], steps[0], path['edges'][i], self.resources_by_parent)
                                i += 1
                    
        #print (self.resources)
        #print (self.resources)    
        #print (self.properties)
        #print (self.properties)
            
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
#cpf.buildMatrix()
#cpf.visualize()
#print (cpf.getPaths('http://dbpedia.org/resource/France'))
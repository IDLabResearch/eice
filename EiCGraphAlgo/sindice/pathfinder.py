'''
Created on 10-aug.-2012

@author: ldevocht
'''
import numpy as np
import scipy
import networkx as nx
from scipy import linalg
from sindice import worker, resourceretriever, graph
import time, gc, sys, logging

logger = logging.getLogger('pathFinder')
query_log = logging.getLogger('query')

''' @params
        source: *
        property: <name>
        value: "Guetta"
        type: foaf:person
    Query: http://api.sindice.com/v3/search?nq=* <name> "Guetta"fq=class:foaf:person&format=json
'''
class PathFinder:
    resources = dict()
    resources_by_parent = dict()
    iteration = 0
    
    def __init__(self,s1,s2,threshold=1.1):
        worker.startQueue(resourceretriever.resourceFetcher, num_of_threads=32)
        self.resources = dict()
        self.resources_by_parent = dict()   
        self.storedResources = dict()  
        self.initMatrix(s1, s2)
        self.threshold = threshold
        
        
    def initMatrix(self, source1, source2):
        query_log.info('Path between {0} and {1}'.format(source1,source2))
        s1 = '<%s>' % source1
        s2 = '<%s>' % source2
        self.resources[0] = s1
        self.resources[1] = s2
        self.stateGraph = np.zeros((2, 2), np.byte)
        self.stateGraph[0] = [1, 0]
        self.stateGraph[1] = [0, 1]
        self.iteration += 1
        return self.stateGraph

    def iterateMatrix(self, blacklist=set()):
        logger.info ('--- NEW ITERATION ---')
        logger.info ('Existing resources {0}'.format(str(len(self.resources))))
        logger.info ('Indexed resources by parents {0}'.format(str(len(self.resources_by_parent))))
        logger.info ('Grandmother: {0}'.format(self.resources[0]))
        logger.info ('Grandfather: {0}'.format(self.resources[1]))
        logger.info ('--- --- ---')
        
        start = time.clock()
        additionalResources = set()
        prevResources = set()
        
        for key in self.resources:
            prevResources.add(self.resources[key])
            
        for resource in prevResources:
            item = [resource, self.resources_by_parent, additionalResources, blacklist]
            worker.getQueue(resourceretriever.resourceFetcher).put(item)
        
        worker.getQueue(resourceretriever.resourceFetcher).join()
        
        toAddResources = list(additionalResources - prevResources)    
        #toAddResources = filter(resourceretriever.isResource, toAddResources)
        
        gc.collect()
        
        logger.info('Updated indexed resources with parents {0}'.format(str(len(self.resources_by_parent))))    
        
        n = len(self.resources)
        
        for resource in toAddResources:
            self.resources[n] = resource
            n = n + 1
            
        logger.info ('Total resources: %s' % str(n))
            
        halt1 = time.clock()
        logger.info ('resource gathering: %s' % str(halt1 - start))
        self.stateGraph = np.zeros(shape=(n, n), dtype=np.byte)
        
        [self.buildGraph(i, n) for i in range(n)]
        halt2 = time.clock()
        logger.info ('graph construction: %s' % str(halt2 - halt1))
        
        #For next iteration, e.g. if no path was found
        #Check for singular values to reduce dimensions of existing resources
        self.storedResources.update(self.resources)
        
        if not graph.pathExists(self.stateGraph) and self.iteration > 1:
            try:
                logger.info ('reducing matrix')
                logger.debug (len(self.stateGraph))
                k = np.int((1-np.divide(1,self.iteration))*250)
                h = (nx.pagerank_scipy(nx.Graph(self.stateGraph), max_iter=100, tol=1e-07))
                res = list(sorted(h, key=h.__getitem__, reverse=True))
                logger.debug(k)
                
                #u, s, vt = scipy.linalg.svd(self.stateGraph.astype('float32'), full_matrices=False)
                
                
                #rank = resourceretriever.rankToKeep(u, s, self.threshold)
                #unimportant resources are unlikely to provide a path
                #unimportant = resourceretriever.unimportantResources(u, rank, s)
                #important = resourceretriever.importantResources(u, rank)

                #print ('error ratio:')                
                #print (np.divide(len(unimportant & important)*100,len(important)))
                unimportant = res[k:]
                self.resources = resourceretriever.removeUnimportantResources(unimportant, self.resources)            
                halt3 = time.clock()
                logger.info ('rank reducing: %s' % str(halt3 - halt2))
                logger.info('Updated resources amount: %s' % str(len(self.resources)))
            except:
                logger.error ('Graph is empty')
                logger.error (sys.exc_info())
        
        logger.info ('total %s' % str(time.clock()-start))
        logger.info ('=== === ===')
        self.iteration+=1
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
            
    def getResourcesByParent(self):
        return self.resources_by_parent
     
    def getGraph(self):
        return self.stateGraph    
    
    def getResources(self):
        return self.storedResources

import numpy as np
import scipy
import networkx as nx
from scipy import linalg, spatial
from core import graph, resourceretriever
import time, gc, sys, logging
from core.worker_pool import Worker
from core.resourceretriever import Resourceretriever

class PathFinder:
    """This class contains the adjacency matrix and provides interfaces to interact with it.
    Besides the adjacency matrix it also holds the fetched resources in a hash set.
    """

    def __init__(self,s1,s2,threshold=1.1):
        """Initialization of all required containers"""
        self.logger = logging.getLogger('pathFinder')
        self.query_log = logging.getLogger('query')
        self.worker = Worker()
        self.resources_s1 = set()
        self.resources_s2 = set()
        self.resources = dict()
        self.resources_inverse_index = dict()
        self.resources_by_parent = dict()   
        self.storedResources = dict()  
        self.threshold = threshold
        self.checked_resources = 0
        self.resourceretriever = Resourceretriever()
        self.iteration = 0
        self.initMatrix(s1, s2)

    def initMatrix(self, source1, source2):
        """Initialization of the adjacency matrix based on input source and destination."""
        self.query_log.info('Path between {0} and {1}'.format(source1,source2))
        s1 = '<%s>' % source1
        s2 = '<%s>' % source2
        self.resources[0] = s1
        self.resources_s1.add(s1)
        self.resources[1] = s2
        self.resources_s2.add(s2)
        self.stateGraph = np.zeros((2, 2), np.byte)
        self.stateGraph[0] = [1, 0]
        self.stateGraph[1] = [0, 1]
        self.iteration += 1
        return self.stateGraph

    def iterateMatrix(self, blacklist=set(), additionalRes = set()):
        """Iteration phase,
        During this phase the children of the current bottom level nodes are fetched and added to the hashed set.
        
        **Parameters**
    
        blacklist : set, optional (default = empty)
            set of resources predicates to exclude from the pathfinding algorithm
        
        additionalResources : set, optional (default = empty)
            set of resources to include anyway in the next iteration
    
        **Returns**
        
        response : stateGraph
            contains the updated adjacency matrix after fetching new resources
        """
        self.logger.info ('--- NEW ITERATION ---')
        self.logger.info ('Existing resources {0}'.format(str(len(self.resources))))
        self.logger.info ('Indexed resources by parents {0}'.format(str(len(self.resources_by_parent))))
        self.logger.info ('Grandmother: {0}'.format(self.resources[0]))
        self.logger.info ('Grandfather: {0}'.format(self.resources[1]))
        self.logger.info ('--- --- ---')
        
        start = time.clock()
        prevResources = set()
        additionalResources = set()
        
        for key in self.resources:
            prevResources.add(self.resources[key])
        
        self.worker.startQueue(self.resourceretriever.fetchResource, num_of_threads=32)
        
        if len(additionalRes) == 0: 
            
            for resource in prevResources:
                item = [resource, self.resources_by_parent, additionalResources, blacklist]
                self.worker.queueFunction(self.resourceretriever.fetchResource, item)
            
            self.worker.waitforFunctionsFinish(self.resourceretriever.fetchResource)
        
        else:
            self.logger.info('Special search iteration: Deep search')
            for resource in additionalRes:
                
                item = [resource, self.resources_by_parent, additionalResources, blacklist]
                self.worker.queueFunction(self.resourceretriever.fetchResource, item)
                
            self.worker.waitforFunctionsFinish(self.resourceretriever.fetchResource)
            
        
        toAddResources = list(additionalResources - prevResources)    
        #toAddResources = filter(resourceretriever.isResource, toAddResources)
        
        gc.collect()
        
        self.logger.info('Updated indexed resources with parents {0}'.format(str(len(self.resources_by_parent))))    
        
        n = len(self.resources)
        
        for resource in toAddResources:
            self.resources[n] = resource
            n = n + 1
            
        self.logger.info ('Total resources: %s' % str(n))

        self.checked_resources += len(additionalResources)
            
        halt1 = time.clock()
        self.logger.info ('resource gathering: %s' % str(halt1 - start))
        self.stateGraph = np.zeros(shape=(n, n), dtype=np.byte)
        
        [self.buildGraph(i, n) for i in range(n)]
        halt2 = time.clock()
        self.logger.info ('graph construction: %s' % str(halt2 - halt1))
        
        #For next iteration, e.g. if no path was found
        #Check for singular values to reduce dimensions of existing resources
        self.storedResources.update(self.resources)
        
        if not graph.pathExists(self.stateGraph) and self.iteration > 1:
            try:
                self.logger.info ('reducing matrix')
                self.logger.debug (len(self.stateGraph))
                k = np.int((1-np.divide(1,self.iteration))*250)
                h = (nx.pagerank_scipy(nx.Graph(self.stateGraph), max_iter=100, tol=1e-07))
                #h = (nx.hits_scipy(nx.Graph(self.stateGraph), max_iter=100, tol=1e-07))
                res = list(sorted(h, key=h.__getitem__, reverse=True))
                self.logger.debug(k)
                
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
                self.logger.info ('rank reducing: %s' % str(halt3 - halt2))
                self.logger.info('Updated resources amount: %s' % str(len(self.resources)))
            except:
                self.logger.error ('Graph is empty')
                self.logger.error (sys.exc_info())
        
        self.logger.info ('total %s' % str(time.clock()-start))
        self.logger.info ('=== === ===')
        self.iteration+=1
        return self.stateGraph
    
    def iterateOptimizedNetwork(self, k = 4):
        for i in self.resources:
            resource = self.resources[i]
            self.resources_inverse_index[resource] = i
            if any(e in self.resources_s1 for e in self.resources_by_parent[resource] ):
                self.resources_s1.add(resource)
            elif any(e in self.resources_s2 for e in self.resources_by_parent[resource] ):
                self.resources_s2.add(resource)
            else:
                self.logger.warning ('resource %s does not belong to any parent' % resource)
          
        start = self.findBestChilds([self.resources_inverse_index[resource] for resource in self.resources_s1], k)
        dest = self.findBestChilds([self.resources_inverse_index[resource] for resource in self.resources_s2], k)
        
        childs = dict() 
        childs['start'] = [self.resources[i] for i in start]
        childs['dest'] = [self.resources[i] for i in dest]
        return childs
    
    def findBestChilds(self,nodes,k = 4):
        n = len(nodes)
        node_list = dict()
        i = 0
        for node in nodes:
            node_list[i] = node
            i += 1
            
        self.stateGraph = np.zeros(shape=(n, n), dtype=np.byte)
        
        [self.buildSubGraph(i, n, node_list) for i in range(n)]

        try:
            self.logger.debug (len(self.stateGraph))
            h = (nx.pagerank_scipy(nx.Graph(self.stateGraph), max_iter=100, tol=1e-07))

            res = list(sorted(h, key=h.__getitem__, reverse=True))

            important = res[:k]          
        except:
            self.logger.error ('Graph is empty')
            self.logger.error (sys.exc_info())
        
        dereffed_list = set([self.sub(i, node_list) for i in important])
        dereffed_list.discard(0)
        dereffed_list.discard(1)
        return list(dereffed_list)
    
    def jaccard_node(self,nodeA,nodeB):
        resA = frozenset(self.resources_by_parent[self.resources[nodeA]])
        resB = frozenset(self.resources_by_parent[self.resources[nodeB]])
        return 1-np.divide(len(resA & resB),len(resA | resB))  
    
    def jaccard_index (self,string1, string2):
        """ Compute the Jaccard index of two strings, in an efficient way.
        """
        set1, set2 = set(string1), set(string2)
        n = len(set1.intersection(set2))
        jacc = n / float(len(set1) + len(set2) - n)
        return jacc


    def jaccard_distance (self,string1, string2):
        """ Compute the Jaccard distance between two strings.
        """
        return 1.0 - self.jaccard_index(string1, string2)
    
    def jaccard(self,nodeA,nodeB):
        """Computes the jaccard between two nodes."""
        respbA = self.resources_by_parent[self.resources[nodeA]].values()
        respbB = self.resources_by_parent[self.resources[nodeB]].values()
        predA = set()
        predB = set()
        for link in respbA:
            predA.add(link['uri'])
            
        for link in respbB:
            predB.add(link['uri'])
        return scipy.spatial.distance.jaccard(np.array(predA), np.array(predB))    
        #return 1-np.divide(len(predA & predB),len(predA | predB))       
    
    def buildGraph(self, i, n):
        """Builds a graph based on row number i and size n"""
        row = np.zeros(n, np.byte)
        [self.matchResource(i, j, row) for j in range(n)]
        self.stateGraph[i] = row
        
    def buildSubGraph(self, i, n, sub_index):
        """Builds a graph based on row number i and size n"""
        row = np.zeros(n, np.byte)
        [self.matchResource(i, j, row, sub_index) for j in range(n)]
        self.stateGraph[i] = row
    
    def sub(self, i, sub_index = None):
        if sub_index == None:
            return i
        else:
            return sub_index[i]
        
    def matchResource(self, i, j, row, sub_index = None):
        """Matches each resource with row and column number i and j in a row from the adjacency matrix"""
        try:
            if i == j:
                row[j] = 1
            elif not self.resources[self.sub(j,sub_index)] in self.resources_by_parent:
                row[j] = 0
            elif i in self.resources:
                if self.resources[self.sub(i,sub_index)] in self.resources_by_parent[self.resources[self.sub(j,sub_index)]]:
                    row[j] = 1
                else:
                    row[j] = 0
            else:
                row[j] = 0
        
        except:
            row[j] = 0
            self.logger.error ('error %s not found in list of resources' % str(j))
            self.logger.error (self.resources)
            self.logger.error (sys.exc_info())
            
    
    def resourceFetcher(self):
        q = self.worker.getQueue(self.resourceFetcher)
        while True:
            item = q.get()
            self.resourceretriever.fetchResource(item[0], item[1], item[2], item[3])
            q.task_done()
                
    def getResourcesByParent(self):
        return self.resources_by_parent
     
    def getGraph(self):
        return self.stateGraph    
    
    def getResources(self):
        return self.storedResources

import scipy, math, io, requests, concurrent.futures, time, gc, sys, logging
import numpy as np
import networkx as nx
from scipy import linalg, spatial
from core.worker_threaded import Worker
from core.resourceretriever import Resourceretriever
from core import graph

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
        self.added = set()
        self.checked_resources = 0
        self.resourceretriever = Resourceretriever()
        self.iteration = 0
        self.initMatrix(s1, s2)
        self.session = requests.session()

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
    
    def handle_request(self, response):
        print('hello %s' % response)
        
    def iterateMatrix(self, blacklist=set(), additionalRes = set(), kp=75):
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
            res = self.resources[key]
            if not self.resources[key] in self.added:
                prevResources.add(res)
            
        #print('previous')
        #print(len(prevResources))
        #print('added')
        #print(len(self.added))
        
        reqs = list()
        
        if len(additionalRes) == 0: 
            
            for resource in prevResources:
                self.added.add(resource)
            for url in self.resourceretriever.genMultiUrls(prevResources):
                reqs.append(url)
                        
        else:
            self.logger.info('Special search iteration: Deep search')
            for resource in additionalRes:
                self.added.add(resource)
            for url in self.resourceretriever.genMultiUrls(additionalRes):
                reqs.append(url)
        
        if len(reqs) > 0: 
            #rs = (grequests.get(u) for u in res['urls'])
            #resps = grequests.map(rs, session=self.session)
            resps = list()
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                for res in reqs:
                    # Start the load operations and mark each future with its URL
                    future_to_url = {executor.submit(requests.get, url): url for url in res['urls']}
                    for future in concurrent.futures.as_completed(future_to_url):
                        url = future_to_url[future]
                        try:
                            response = dict()
                            response['resources'] = res['resources']
                            response['results'] = future.result()
                            resps.append(response)
                        except Exception as exc:
                            self.logger.error('%r generated an exception: %s' % (url, exc))
                        else:
                            self.logger.debug('retrieved results for %r' % (url))
                #todo move http gets in threads vs async grequests
                
            self.worker.startQueue(self.resourceretriever.processMultiResource, num_of_threads=64)    
            
            for rp in resps:
            #for rp in res['urls']:
                item = [rp['resources'], rp['results'], self.resources_by_parent, additionalResources, blacklist]
                self.worker.queueFunction(self.resourceretriever.processMultiResource, item)    
            
            self.worker.waitforFunctionsFinish(self.resourceretriever.processMultiResource)
            
        toAddResources = list(additionalResources - prevResources)    
        #toAddResources = filter(resourceretriever.isResource, toAddResources)
       
        gc.collect()
        
        self.logger.info('Updated indexed resources with parents {0}'.format(str(len(self.resources_by_parent))))    
        
        n = len(self.resources)
        
        self.logger.debug ('Total resources before update: %s' % str(n))
        #print ('Total resources before update: %s' % str(n))
        
        for resource in toAddResources:
            self.resources[n] = resource
            n = n + 1
            
        self.logger.debug ('Total resources after update: %s' % str(n))
        #print ('Total resources after update: %s' % str(n))

        self.checked_resources += len(additionalResources)
            
        halt1 = time.clock()
        self.logger.info ('resource gathering: %s' % str(halt1 - start))
        #print ('resource gathering: %s' % str(halt1 - start))
        self.stateGraph = np.zeros(shape=(n, n), dtype=np.byte)
        
        [self.buildGraph(i, n) for i in range(n)]
        halt2 = time.clock()
        self.logger.info ('graph construction: %s' % str(halt2 - halt1))
        #print ('graph construction: %s' % str(halt2 - halt1))
        #For next iteration, e.g. if no path was found
        #Check for singular values to reduce dimensions of existing resources
        self.storedResources.update(self.resources)
        
        if not graph.pathExists(self.stateGraph) and self.iteration > 1:
            try:
                self.logger.info ('reducing matrix')
                self.logger.debug (len(self.stateGraph))
                #k = self.iteration*kp
                k = int(kp*math.pow(1.2,self.iteration))
                #print ('reducing matrix, max important nodes')
                #print (k)
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
                self.resources = self.removeUnimportantResources(unimportant)            
                halt3 = time.clock()
                self.logger.info ('rank reducing: %s' % str(halt3 - halt2))
                self.logger.info('Updated resources amount: %s' % str(len(self.resources)))
                #print ('Updated resources amount after reduction: %s' % str(len(self.resources)))
            except:
                self.logger.error ('Graph is empty')
                self.logger.error (sys.exc_info())
        
        self.logger.info ('total %s' % str(time.clock()-start))
        self.logger.info ('=== === ===')
        #print ('=== === ===')
        self.iteration+=1
        return self.stateGraph
    
    def iterateOptimizedNetwork(self, k = 4):
        for i in self.resources:
            resource = self.resources[i]
            self.resources_inverse_index[resource] = i
            if (resource in self.resources_by_parent):
                if any(e in self.resources_s1 for e in self.resources_by_parent[resource] ):
                    self.resources_s1.add(resource)
                elif any(e in self.resources_s2 for e in self.resources_by_parent[resource] ):
                    self.resources_s2.add(resource)
                else:
                    self.logger.warning ('resource %s does not belong to any parent' % resource)
            else:
                self.logger.warning ('resource %s has no children' % resource)
          
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
        if len(dereffed_list) > 1:
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
        return spatial.distance.jaccard(np.array(predA), np.array(predB))    
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
            
    def removeUnimportantResources(self, unimportant):
        updated_resources = dict()
        for u in unimportant:
            #Never delete grandmother and grandfather, even if they become insignificant
            if u > 1: 
                del self.resources[u]
        i = 0
        for r in self.resources:
            updated_resources[i] = self.resources[r]
            i += 1        
        resources = updated_resources
        return resources
            
    
    def resourceFetcher(self):
        q = self.worker.getQueue(self.resourceFetcher)
        while True:
            item = q.get()
            self.resourceretriever.fetchResource(item[0], item[1], item[2], item[3])
            q.task_done()
            
    def findPath(self):
        return graph.path(self)
                
    def getResourcesByParent(self):
        return self.resources_by_parent
     
    def getGraph(self):
        return self.stateGraph    
    
    def getResources(self):
        return self.storedResources

import numpy as np
import scipy
import math
#import networkx as nx
import graph_tool.all as gt
from scipy import linalg, spatial
from core import graph_gt, resourceretriever_gt
from core.graph_gt import Graph
import time, gc, sys, logging
from core.worker_threaded import Worker
from core.resourceretriever_gt import Resourceretriever
import operator
import requests
import concurrent.futures

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
        self.threshold = threshold
        self.checked_resources = 0
        self.resourceretriever = Resourceretriever()
        self.iteration = 0
        self.initMatrix(s1, s2)
        self.unimportant = set()
        self.added = set()
        self.session = requests.session()
        self.graph = Graph()

    def initMatrix(self, source1, source2):
        """Initialization of the adjacency matrix based on input source and destination."""
        self.query_log.info('Path between {0} and {1}'.format(source1,source2))
        s1 = '<%s>' % source1
        s2 = '<%s>' % source2

        self.stateGraph = gt.Graph(directed=False)
        self.source = self.stateGraph.add_vertex()
        self.target = self.stateGraph.add_vertex()
        #self.stateGraph.add_edge(self.source, self.target)
        self.resources = self.stateGraph.new_vertex_property("string")
        self.resources_by_parent = self.stateGraph.new_edge_property("object")
        self.resources[self.source] = s1
        self.resources_inverse_index[s1] = self.source
        self.resources_s1.add(s1)
        self.resources[self.target] = s2
        self.resources_inverse_index[s2] = self.target
        self.resources_s2.add(s2)
        self.iteration += 1
        return self.stateGraph

    def iterateMatrix(self, blacklist=set(), additionalRes = set(),kp=75):
        """Iteration phase,
        During this phase the children of the current bottom level nodes are fetched and added to the hashed set.
        
        **Parameters**
    
        blacklist : set, optional (default = empty)
            set of resources predicates to exclude from the pathfinding algorithm
        
        additionalResources : set, optional (default = empty)
            set of resources to include anyway in the next iteration
    
        **Returns**
        
        response : stateGraph
            contains the updated stategraph after fetching new resources
        """
        self.logger.info ('--- NEW ITERATION ---')
        #self.logger.info ('Existing resources {0}'.format(str(len(self.resources.property_list()))))
        #self.logger.info ('Indexed resources by parents {0}'.format(str(len(self.resources_by_parent))))
        self.logger.info ('Grandmother: {0}'.format(self.resources[self.stateGraph.vertex(0)]))
        self.logger.info ('Grandfather: {0}'.format(self.resources[self.stateGraph.vertex(1)]))
        self.logger.info ('--- --- ---')
        
        start = time.clock()
        prevResources = set()
        additionalResources = dict()
        i = 0
        for v in self.stateGraph.vertices():
            i += 1
            if not v in self.added and not v in self.unimportant:
                prevResources.add(self.resources[v])
        
        #print('unimportant') 
        #print(len(self.unimportant))       
        #print('previous')
        #print(len(prevResources))
        #print(prevResources)
        #print('new')
        #print(len(self.added - prevResources))
        #print(self.added)
        #print('added')
        #print(len(self.added))
        #print('total')
        #print(i)
        
        #self.worker.startQueue(self.resourceretriever.fetchResource, num_of_threads=32)
        
        #if len(additionalRes) == 0: 
            
        #    for resource in prevResources:
        #        self.added.add(resource)
        #        item = [resource, additionalResources, blacklist]
        #        self.worker.queueFunction(self.resourceretriever.fetchResource, item)
            
        #    self.worker.waitforFunctionsFinish(self.resourceretriever.fetchResource)
        
        #else:
        #    self.logger.info('Special search iteration: Deep search')
        #    for resource in additionalRes:
        #        self.added.add(resource)
        #        item = [resource, additionalResources, blacklist]
        #        self.worker.queueFunction(self.resourceretriever.fetchResource, item)
                
        #    self.worker.waitforFunctionsFinish(self.resourceretriever.fetchResource)
            
        
        
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
            resps = set()
            with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
                for res in reqs:
                    # Start the load operations and mark each future with its URL
                    future_to_url = {executor.submit(requests.get, url): url for url in res['urls']}
                    for future in concurrent.futures.as_completed(future_to_url):
                        url = future_to_url[future]
                        try:
                            resps.add(future.result())
                        except Exception as exc:
                            self.logger.error('%r generated an exception: %s' % (url, exc))
                        else:
                            self.logger.debug('%r page' % (url))
          
            self.worker.startQueue(self.resourceretriever.processMultiResource, num_of_threads=16)
                            
            for rp in resps:
            #for rp in res['urls']:
                item = [res, rp, self.resources_by_parent, additionalResources, blacklist]
                self.worker.queueFunction(self.resourceretriever.processMultiResource, item)    
        
            self.worker.waitforFunctionsFinish(self.resourceretriever.processMultiResource)
        
        #toAddResources = list(additionalResources.keys() - prevResources) 
        #print('to add resources')
        #print(len(toAddResources))
        #toAddResources = filter(resourceretriever.isResource, toAddResources)
        
        gc.collect()
        
        #self.logger.info('Updated indexed resources with parents {0}'.format(str(len(self.resources_by_parent.list_properties()))))    
            
        self.logger.info ('Total resources: %s' % str(len(prevResources)))

        self.checked_resources += len(additionalResources)
            
        halt1 = time.clock()
        self.logger.info ('resource gathering: %s' % str(halt1 - start))
        #print ('resource gathering: %s' % str(halt1 - start))
        #self.stateGraph = gt.Graph()
        #vlist = self.stateGraph.add_vertex(len(toAddResources))
        #[self.buildGraph(ri, self.stateGraph) for ri in ris]
        #gt.graph_draw(self.stateGraph, vertex_text=self.stateGraph.vertex_index, vertex_font_size=10,
        #           output_size=(800,800), output="two-nodes.pdf")
        
        [self.addDirectedLink(res, additionalResources, self.stateGraph) for res in prevResources]
                    
        halt2 = time.clock()
        self.logger.info ('graph construction: %s' % str(halt2 - halt1))
        #print ('graph construction: %s' % str(halt2 - halt1))
        #For next iteration, e.g. if no path was found
        #Check for singular values to reduce dimensions of existing resources
        #gt.graph_draw(self.stateGraph, vertex_text=self.stateGraph.vertex_index, vertex_font_size=10,
        #           output_size=(800,800), output="two-nodes.pdf")
        #pathExists = self.graph.pathExists(self)
        #self.logger.debug('path exists: %s' % pathExists)
        self.logger.debug('current iteration: %s' % self.iteration)
        if self.iteration > 1:
            try:
                self.logger.info ('reducing matrix')
                #print ('reducing matrix, max important nodes')
                #self.logger.debug (len(self.stateGraph))
                #k = np.int((1-np.divide(1,self.iteration))*500)
                #k = np.int((1-np.divide(1,self.iteration))*kp)
                k = int(kp*math.pow(1.2,self.iteration))
                #print (k)
                h = gt.pagerank(self.stateGraph)

                #h = (nx.pagerank_scipy(nx.Graph(self.stateGraph), max_iter=100, tol=1e-07))
                #h = (nx.hits_scipy(nx.Graph(self.stateGraph), max_iter=100, tol=1e-07))
                vertices = dict()
                for vertex in self.stateGraph.vertices():
                    vertices[self.stateGraph.vertex_index[vertex]] = h[vertex]
                #print(vertices)
                res = list(sorted(vertices, key=vertices.__getitem__, reverse=True))
                #print (res)
                self.logger.debug(k)
                unimportant = res[k:]
                self.unimportant = set()
                for u in unimportant:
                    #Never delete grandmother and grandfather, even if they become insignificant
                    if u > 1:
                        self.unimportant.add(self.stateGraph.vertex(u))
                        #pass
                #print(self.unimportant)
                #self.stateGraph = resourceretriever_gt.removeUnimportantResources(unimportant, self.resources, self.stateGraph)            
                halt3 = time.clock()
                self.logger.info ('rank reducing: %s' % str(halt3 - halt2))
                #self.logger.info('Updated resources amount: %s' % str(len(self.stateGraph.vertices())))
                #print('Updated resources amount: %s' % str(len(self.stateGraph.vertices())))
                #print(len(self.unimportant))
            except:
                self.logger.error ('Pathfinding reduction error')
                self.logger.error (sys.exc_info())
        else:
            self.logger.info ('no rank reducing')
        
        self.logger.info ('total %s' % str(time.clock()-start))
        self.logger.info ('=== === ===')
        self.iteration+=1
        return self.stateGraph
    
    def addDirectedLink(self, res, additionalResources, stateGraph, sub_index = False, sub_parent_index = False, sub_added = False):            
        if res in additionalResources:
            vi = self.resources_inverse_index[res]
            for newLink in additionalResources[res]:
                if not newLink.targetRes in self.resources_inverse_index:
                    vj = stateGraph.add_vertex()
                else:
                    vj = self.resources_inverse_index[newLink.targetRes]

                
                e = stateGraph.add_edge(vi,vj)
                if sub_index:
                    sub_index[vj] = newLink.targetRes
                else:
                    self.resources[vj] = newLink.targetRes
                    self.resources_inverse_index[newLink.targetRes] = vj
                link = dict()
                link['uri'] = newLink.predicate
                link['inverse'] = newLink.inverse
                
                if sub_index:
                    sub_parent_index[e] = link
                else:
                    self.resources_by_parent[e] = link

    def iterateOptimizedNetwork(self, k = 4):
        for i in self.stateGraph.vertices():
            resource = self.resources[i]
            self.resources_inverse_index[resource] = i
            if any(e in self.resources_s1 for e in resource.out_edges() ):
                self.resources_s1.add(resource)
            elif any(e in self.resources_s2 for e in self.resources_by_parent[i] ):
                self.resources_s2.add(resource)
            else:
                self.logger.warning ('resource %s does not belong to any parent' % resource)
          
        start = self.findBestChilds([self.resources_inverse_index[resource] for resource in self.resources_s1], k)
        dest = self.findBestChilds([self.resources_inverse_index[resource] for resource in self.resources_s2], k)
        
        childs = dict() 
        childs['start'] = [self.resources[i] for i in start]
        childs['dest'] = [self.resources[i] for i in dest]
        return childs
    
    def resolvePath(self, path,resources,resourcesByParents,stateGraph):
        """Resolves a path between two resources.
        
        **Parameters**
        
        path : list of numbers corresponding with resources list indices
        resources : list of resources containing hashes to the resources
        
        **Returns**
        
        resolvedPath : sequential list of hashes of the nodes in the path
        
        """
        resolvedPath = list()
        resolvedLinks = list()
        steps = list()
        links = list()
        v = self.target
        while v != self.source:
            p = stateGraph.vertex(path[v])
            for e in v.out_edges():
                if e.target() == p and not v in steps:
                    steps.append(v)
                    links.append(e)
            v = p
        steps.append(self.source)
        steps.reverse()
        for step in steps:
            resolvedPath.append(resources[step])
        for link in links:
            try:
                resolvedLinks.append(resourcesByParents[link])
            except:
                logging.error ('%s not found' % link)
        #print (resolvedPath[:10])
        #print (resolvedLinks[:10])
        return (resolvedPath,resolvedLinks)
    
    def findBestChilds(self,nodes,k = 4):
        stateGraph = gt.Graph()
        node_list = stateGraph.new_vertex_property("string")
        node_parents = stateGraph.new_edge_property("object")
        
        [self.addDirectedLink(node, nodes, stateGraph, node_list, node_parents) for node in nodes]

        try:
            #self.logger.debug (len(stateGraph))
            h = gt.pagerank(stateGraph)
            
            res = list(sorted(h, key=h.__getitem__, reverse=True))
            
            vertices = dict()
            for vertex in stateGraph.vertices():
                vertices[stateGraph.vertex_index[vertex]] = h[vertex]

            res = list(sorted(vertices, key=vertices.__getitem__, reverse=True))

            important = res[:k]
            important.remove(0)
            important.remove(1)
            important_v = set()
            [important_v.add(stateGraph.vertex(i)) for i in important]          
        except:
            self.logger.error ('Graph is empty')
            self.logger.error (sys.exc_info())
        
        dereffed_list = set([node_list[i] for i in important_v])
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
        respbA = set()
        respbB = set()
        for e in nodeA.out_edges():
            link = self.resources_by_parent[e]
            if link:
                respbA.add(link['uri'])
            
        for f in nodeB.out_edges():
            link = self.resources_by_parent[f]
            if link:
                respbB.add(link['uri'])
                
        """Computes the jaccard between two nodes."""
        return scipy.spatial.distance.jaccard(np.array(respbA), np.array(respbB))    
        #return 1-np.divide(len(predA & predB),len(predA | predB))       
    
    def buildGraph(self, vi, stateGraph, sub_index = False):
        """Builds a graph based on row number i and size n"""
        [self.matchResource(vi, vj, stateGraph, sub_index) for vj in stateGraph.vertices()]
    
    def createResource(self, resource, v = False, sub_index = False):
        if sub_index:
            sub_index[v] = resource
        else:
            self.resources[v] = resource
        return v

    def matchResource(self, vi, vj, stateGraph = False, sub_index = False):
        """Matches each resource with row and column number i and j in a row from the adjacency matrix"""
        #i = stateGraph.vertex_index[vi]
        #j = stateGraph.vertex_index[vj]
        
        if sub_index:
            resources = sub_index
        else:
            resources = self.resources
            
        try:
            #if vi == vj:
            #    stateGraph.add_edge(vi,vj)
            if not resources[vj] in self.resources_by_parent:
                pass
            elif vi in resources and vj in resources:
                if resources[vi] in self.resources_by_parent[resources[vj]]:
                    stateGraph.add_edge(vi,vj)
                else:
                    pass
            else:
                pass
        
        except:
            self.logger.error ('error %s not found in list of resources' % str(stateGraph.vertex_index[vj]))
            #self.logger.error (self.resources)
            #self.logger.error (sys.exc_info())
            
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
        return self.resources

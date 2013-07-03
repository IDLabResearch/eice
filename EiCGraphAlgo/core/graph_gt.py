import numpy as np
import graph_tool.all as gt
import matplotlib.cm
import sys
import math
import random
from itertools import islice, chain
import logging

logger = logging.getLogger('pathFinder')



def resolvePath(path,resources,stateGraph):
    """Resolves a path between two resources.
    
    **Parameters**
    
    path : list of numbers corresponding with resources list indices
    resources : list of resources containing hashes to the resources
    
    **Returns**
    
    resolvedPath : sequential list of hashes of the nodes in the path
    
    """
    resolvedPath = list()
    steps = list()
    v = stateGraph.vertex(1)
    while v != stateGraph.vertex(0):
        p = stateGraph.vertex(path[v])
        for e in v.out_edges():
            if e.target() == p:
                steps.append(v)
        v = p
    steps.append(stateGraph.vertex(0))
    steps.reverse()
    for step in steps:
        resolvedPath.append(resources[step])
    print (resolvedPath[:10])
    return resolvedPath

def batch(iterable, size):
    sourceiter = iter(iterable)
    while True:
        batchiter = islice(sourceiter, size)
        yield chain([next(batchiter)], batchiter)

def rolling_window(seq, window_size):
    it = iter(seq)
    win = [next(it) for cnt in range(window_size)] # First window
    yield win
    for e in it: # Subsequent windows
        win[:-1] = win[1:]
        win[-1] = e
        yield win
        
def resolveLinks(resolvedPath,resourcesByParent):
    """Resolves the links in a path between two resources.
    
    **Parameters**
    
    resolvedPath : list of hash corresponding with resources in the path
    resourcesByParent : map that contains a list of hashes with the corresponding sets of children for each parent
    
    **Returns**
    
    resolvedLinks : sequential list of predicates (URIs) connecting the resources in the path
    
    """
    resolvedLinks = list()

    for iterator in rolling_window(resolvedPath, 2):
        steps = list(iterator)
        #logger.debug (steps)
        if len(steps) == 2:
            try:
                resolvedLinks.append((resourcesByParent[steps[0]][steps[1]])['uri'][1:-1])
            except:
                logger.error('could not find relation between %s and %s ' % (steps[0],steps[1]) )
                #print(resourcesByParent[steps[0]])
    return resolvedLinks
                                                   
def listPath(resolvedPath,resourcesByParent):
    """Converts a resolved path containing hashes of the resources to the actual URIs of each resource"""
    resolvedEdges = list()
    listedPath = list()
    for iterator in rolling_window(resolvedPath, 2):
        steps = list(iterator)
        #logger.debug (steps)
        if len(steps) == 2:
            try:
                resolvedEdges.append(resourcesByParent[steps[0]][steps[1]])
            except:
                logger.error('could not find relation between %s and %s ' % (steps[0],steps[1]) )
                #print(resourcesByParent[steps[0]])
            
    for node in resolvedPath:
        step = dict()
        step['uri'] = node.strip('<>')
        step['type'] = 'node'
        listedPath.append(step)
        if len(resolvedEdges) > 0:
            step = dict()
            step['uri'] = resolvedEdges[0]['uri'].strip('<>')
            step['type'] = 'link'
            step['inverse'] = resolvedEdges[0]['inverse']
            listedPath.append(step)
            del resolvedEdges[0]
    return listedPath

def pathExists(M):
    """Checks whether an adjacency matrix M contains a path or not"""
    #print('Checking if path exists')
    dist = gt.shortest_distance(M,source=M.vertex(0),target=M.vertex(1))
    return dist < 100

def pathLength(pathFinder):
    """Checks the length of a path if it exists in the given PathFinder class"""
    G = pathFinder.getGraph()
    try:
        if pathExists(G):
            target = G.vertex(1)
            G, weight = buildWeightedGraph(pathFinder)
            touch_v = G.new_vertex_property("bool")
            touch_e = G.new_edge_property("bool")
            dist, pred = gt.astar_search(G, G.vertex(0), weight,
                                 VisitorExample(touch_v, touch_e, target),
                                 heuristic=lambda v: pathFinder.jaccard(v, target))
            return dist
        else:
            return -1
    except:
        logger.error (sys.exc_info())
        return None

def path(pathFinder):
    """Computes the astar path if it exists in the given PathFinder class"""
    G = pathFinder.getGraph()
    target = G.vertex(1)
    try:
        if pathExists(G):
            G, weight = buildWeightedGraph(pathFinder)
            #for vertex in G.vertices():
            #    print (vertex)
            touch_v = G.new_vertex_property("bool")
            touch_e = G.new_edge_property("bool")
            dist, pred = gt.astar_search(G, G.vertex(0), weight,
                                 VisitorExample(touch_v, touch_e, target),       
                                 heuristic=lambda v: pathFinder.jaccard(v, target))
            #print ([pred])
            return [pred]
            #return list(nx.all_simple_paths(G,0,1,cutoff=8))
        else:
            return None
        
    except:
        logger.error (sys.exc_info())
        return None
    
def buildWeightedGraph(pathFinder):
    """Computes the weights for the links in the given PathFinder class"""
    G = pathFinder.getGraph()
    weight = G.new_edge_property("double")
    for e in G.edges():
        weight[e] = math.log(e.source().out_degree()+e.target().out_degree())
    return G, weight

class VisitorExample(gt.AStarVisitor):

    def __init__(self, touched_v, touched_e, target):
        self.touched_v = touched_v
        self.touched_e = touched_e
        self.target = target

    def discover_vertex(self, u):
        self.touched_v[u] = True

    def examine_edge(self, e):
        self.touched_e[e] = True

    def edge_relaxed(self, e):
        if e.target() == self.target:
            raise gt.StopSearch()
    
def visualize(pathFinder, source=False, target=False):
    g, weight = buildWeightedGraph(pathFinder)
    ecolor = g.new_edge_property("string")
    ewidth = g.new_edge_property("double")
    ewidth.a = 1
    touch_v = g.new_vertex_property("bool")
    touch_e = g.new_edge_property("bool")
    if not source:
        source = g.vertex(0)
    if not target:
        target = g.vertex(1)
    dist, pred = gt.astar_search(g, source, weight,
                                 VisitorExample(touch_v, touch_e, target),       
                                 heuristic=lambda v: pathFinder.jaccard(v, target))
    for e in g.edges():
        ecolor[e] = "blue" if touch_e[e] else "black"
    v = target
    while v != g.vertex(0):
        p = g.vertex(pred[v])
        for e in v.out_edges():
            if e.target() == p:
                ecolor[e] = "#a40000"
                ewidth[e] = 3
        v = p
    gt.graph_draw(g, output_size=(600, 600), vertex_fill_color=touch_v, edge_color=ecolor,
                  edge_pen_width=ewidth, output="astar-demo.pdf")
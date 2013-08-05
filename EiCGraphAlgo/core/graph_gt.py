import numpy as np
import graph_tool.all as gt
import matplotlib.cm
import sys
import math
import random
from itertools import islice, chain
import logging

logger = logging.getLogger('pathFinder')

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
                                                   
def listPath(resolvedPath,resolvedLinks):
    """Converts a resolved path containing hashes of the resources to the actual URIs of each resource"""
    resolvedEdges = resolvedLinks
    listedPath = list()
            
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

class Graph():
    def pathExists(self, pathFinder):
        """Checks whether an adjacency matrix M contains a path or not"""
        G = pathFinder.getGraph()
        target = pathFinder.target
        source = pathFinder.source
        logger.debug('Checking if path exists between %s and %s' % (source,target))
        try:
            dist = gt.shortest_distance(G,source=source,target=target)
        except:
            logger.error (sys.exc_info())
        logger.debug('Found distance %s' % dist)
        return dist < 100
    
    def pathLength(self, pathFinder):
        """Checks the length of a path if it exists in the given PathFinder class"""
        G = pathFinder.getGraph()
        target = pathFinder.target
        source = pathFinder.source
        try:
            if self.pathExists(pathFinder):
                G, weight = buildWeightedGraph(pathFinder)
                touch_v = G.new_vertex_property("bool")
                touch_e = G.new_edge_property("bool")
                dist, pred = gt.astar_search(G, source, weight,
                                     VisitorExample(touch_v, touch_e, target),
                                     heuristic=lambda v: pathFinder.jaccard(v, target))
                return dist
            else:
                return -1
        except:
            logger.error (sys.exc_info())
            return None
    
    def path(self, pathFinder):
        """Computes the astar path if it exists in the given PathFinder class"""
        G = pathFinder.getGraph()
        target = pathFinder.target
        source = pathFinder.source
        try:
            if self.pathExists(pathFinder):
                G, weight = buildWeightedGraph(pathFinder)
                #for vertex in G.vertices():
                #    print (vertex)
                touch_v = G.new_vertex_property("bool")
                touch_e = G.new_edge_property("bool")
                dist, pred = gt.astar_search(G, source, weight,
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
        source = pathFinder.source
    if not target:
        target = pathFinder.target
    dist, pred = gt.astar_search(g, source, weight,
                                 VisitorExample(touch_v, touch_e, target),       
                                 heuristic=lambda v: pathFinder.jaccard(v, target))
    for e in g.edges():
        ecolor[e] = "blue" if touch_e[e] else "black"
    v = target
    while v != source:
        p = g.vertex(pred[v])
        for e in v.out_edges():
            if e.target() == p:
                ecolor[e] = "#a40000"
                ewidth[e] = 3
        v = p
    gt.graph_draw(g, output_size=(600, 600), vertex_fill_color=touch_v, edge_color=ecolor,
                  edge_pen_width=ewidth, output="astar-demo.pdf")
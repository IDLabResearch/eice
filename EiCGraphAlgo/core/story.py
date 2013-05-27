from core import storyteller,resourceretriever,graph
import time
import gc
import logging
import pickle
import copy
import numpy as np
import matplotlib.pyplot as plt
import os, sys
import networkx as nx
import string


logger = logging.getLogger('pathFinder')
query_log = logging.getLogger('query')

blacklist = resourceretriever.blacklist

def buildStory(p,start,dest,O,S):
    X = p.generateDescriptor(start)
    Y = p.generateDescriptor(dest)
    
    #for s in S:
    #    print (p.set_definitions[s])
    
    print (start)
    for x in X:
        print (p.set_definitions[x])
    
    print (dest)    
    for y in Y:
        print (p.set_definitions[y])
        
    OL = set()
    CL = set()
    
    Fs = list(S.keys() - X)
    Fx = list(X)
    
    n = len(Fs)
    d = len(Fx)
    
    Ox = None
    for x in X:
        if Ox == None:
            Ox = S[x]
        else:
            Ox = set(Ox).intersection(S[x])
    O_x = set(O.values()) - Ox
    
    print (Ox)
    
    print (O_x)
    
    print (d)
    print (n)
    
    class FeatureBranch:
        parent = None
        root = None
        objs = None
        excludes = None
        includes = None
        yes = None
        no = None
        
        def __init__(self):
            self.yes = set()
            self.no = set()
            self.objs = set()
            self.excludes = set()
            self.includes = set()
            parent = None
            root = None
            
        def __str__(self):
            if self.yes == None and self.no == None:
                return '(%s o: %s incl: %s excl: %s)' % (str(self.root), self.objs, str(self.includes), str(self.excludes))
            else:
                return '(%s incl: %s excl: %s)' % (str(self.root), str(self.includes), str(self.excludes))
        
        def __repr__(self):
            return str(self)
 
    def gen_tree_list(tree, trees=list()):
        if tree == None:
            return []
        else:
            trees = trees
            trees.append(tree.yes)
            trees = trees + gen_tree_list(tree.yes,trees)
            trees.append(tree.no)
            trees = trees + gen_tree_list(tree.no,trees)
            return trees
    
    def recursive_tree_gen(objs,o_descriptors,f_branches,parent_features=list(),remaining_features=list(),includes=set(),excludes=set(),feature=None,tree=None):
        
        tree = FeatureBranch()
        tree.root = feature
        tree.includes = set(copy.copy(includes))
        tree.excludes = set(copy.copy(excludes))
        tree.parent = tree
        print ('Creating tree: %s' % tree.root)
        parent_features.append(feature)
        tree.objs = objs
        print ('Remaining features: %s' % remaining_features)
        if len(remaining_features) > 2 and len(objs) > 1:
            next_feature_y = remaining_features.pop()
            next_feature_n = remaining_features.pop()
            next_objs_y = set()
            next_objs_n = set()
            print ('Next feature y: %s n: %s' % (next_feature_y, next_feature_n))
            for o in objs:
                if o in f_branches[feature].yes:
                    next_objs_y.add(o)
                else:
                    next_objs_n.add(o)
            print ('objects: %s' % objs)
            print ('next objects y: %s n: %s' % (next_objs_y, next_objs_n))
            if len(next_objs_y) > 0:
                incl = copy.copy(tree.includes)
                incl.add(feature)
                tree.yes = (recursive_tree_gen(next_objs_y,o_descriptors,f_branches,parent_features,remaining_features,incl,tree.excludes,next_feature_y))
            else:
                tree.yes = None
            if len(next_objs_n) > 0:
                excl = copy.copy(tree.excludes)
                excl.add(feature) 
                tree.no = (recursive_tree_gen(next_objs_n,o_descriptors,f_branches,parent_features,remaining_features,tree.includes,excl,next_feature_n))
            else:
                tree.no = None
        
            return tree
            
        else:
            tree.yes = None
            tree.no = None
            return tree
        
        
    def construct_tree(j,O,F):
        O = list(O.values())
        o_descriptors = dict()
        f_branches = dict()
        d = len(F)
        for o in O:
            o_descriptors[o] = p.generateDescriptor(o)
                    
        print (o_descriptors)
        node_labels=[F[j] for j in range(d)]
        print (node_labels)
        F = list(F)
        for f in F:
            f_branches[f]=FeatureBranch()
            for o in O:
                if f in o_descriptors[o]:
                    f_branches[f].yes.add(o)
                else:
                    f_branches[f].no.add(o)
        working_item = F[j]
        print (len(F))

        print (working_item)
            
        tree = recursive_tree_gen(O, o_descriptors, f_branches, list(), list(F), set(), set(), working_item)
        trees = list()
        
        trees = gen_tree_list(tree, trees)

        for tree in trees:
            print (tree)
        
#        DG = nx.DiGraph()
#        
#        
#        
#        DG.add_edge(1,2,color='blue',label='yes')
#        DG.add_edge(1,3,color='blue',label='yes')
#        pos=nx.spectral_layout(DG)
#        plt.figure(figsize=(16,16))
#        labels = dict()
#        for node in DG.nodes():
#            labels[node] = p.set_definitions[F[node]]
#        nx.draw(DG,pos,labels = labels,font_size=8)
#        plt.savefig('test.png')
        
    
    
    construct_tree(0,O,Fx)
    construct_tree(0,O,Fs)

def story(start,dest):
    """Creates a story between two resources start and dest

    **Parameters**
    
    start : uri
        resource to start storytelling
    destination : uri
        destination resource for storytelling

    **Returns**
    
    response : dictionary
        contains execution time, path if found, hash

    """
    #START
    start_time = time.clock()
    
    #Initialization
    d = 2 #tree depth
    p = storyteller.Storyteller(start,dest)
    for i in range(d-1):
        p.iterateMatrix(blacklist) #get children of start and destination
    stories = None #Initially no stories exist

    O = p.iterateMatrix(blacklist)
    S = p.getObjectSets()
    
    print (O)
    print (S)
    
    #stories = buildStory(p,start,dest,F,S)
    
    #Following iterations
    while True:
        if not stories == None:
            if len(stories) > 0:
                break
        
        logger.info ('=== %s-- ===' % str(p.iteration))
        gc.collect()
        m = p.iterateMatrix(blacklist)
        halt_path = time.clock()
        stories = graph.path(p)
        logger.info ('Looking for path: %s' % str(time.clock()-halt_path))
        if p.iteration == 10:
            break
    resolvedPaths = list()
    
    #FINISH
    if stories:
        for path in stories:
    #       logger.debug(path)
            resolvedPath = graph.resolvePath(path,p.getResources())
            resolvedLinks = graph.resolveLinks(resolvedPath, p.getResourcesByParent())
            formattedPath = list()
            for step in resolvedPath:
                formattedPath.append(step[1:-1])
            fullPath = dict()
            fullPath['vertices'] = formattedPath
            fullPath['edges'] = resolvedLinks
            resolvedPaths.append(fullPath)
    else:
        return {'path':False,'execution_time':int(round((time.clock()-start_time) * 1000))}
            
    #    graph.visualize(p, path=path)
    finish = int(round((time.clock()-start_time) * 1000))
    r = dict()
    r['execution_time'] = finish
    r['stories'] = resolvedPaths
    r['source'] = start
    r['destination'] = dest
    r['checked_resources'] = p.checked_resources
    r['hash'] = 'h%s' % hash('{0}{1}{2}'.format(start_time,dest,time.time()))
    r['path'] = graph.listPath(resolvedPath,p.getResourcesByParent())
    
    try:
        path = os.path.dirname(os.path.abspath(__file__))
        file = r['hash']
        pickle.dump(r,open("{0}/stored_paths/{1}.dump".format(path,file),"wb"))
    except:
        logger.warning('could not log and store path between {0} and {1}'.format(start,dest))
        logger.error(sys.exc_info())
    query_log.info(r)
    logger.debug(r)
    result = dict()
    result['path'] = r['path']
    result['hash'] = r['hash']
    result['execution_time'] = r['execution_time']
    return result

print (story('http://dbpedia.org/resource/Brussels','http://dbpedia.org/resource/Belgium'))
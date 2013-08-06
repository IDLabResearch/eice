from itertools import islice, chain
import re

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
        
def chunks(l, n):
    return [l[i:i+n] for i in range(0, len(l), n)]

def isResource(item):               
    if '<' in item and not '^' in item:
        return True
    else:
        return False
    
def cleanInversResultSetFast(resultSet, target):
    resultSets = re.split(' .\n',resultSet)
    try:    
        nt_cleaned = dict()
        i = 0
        for row in resultSets[:-1]:
            triple = re.split(' ',row)
            if triple[2] == "<%s>" % target:
                nt_cleaned[i] = triple
                i += 1
    except:
        #print (sys.exc_info())
        #logger.warning('Parsing inverse failed for %s' % target)
        nt_cleaned = False
    return nt_cleaned        
        
def cleanResultSet(resultSet):
    nt_cleaned = dict()
    resultSet = set(resultSet)
    i = 0
    for triple in resultSet:
        triple = triple.strip(' .\n')
        triple = triple.split(' ', 2)
        triple[2] = triple[2].replace('"', '')
        nt_cleaned[i] = triple
        i += 1
    return nt_cleaned  
    
def cleanMultiResultSet(resultSet, targets):#
    resultSets = re.split(' .\n',resultSet)
    try:    
        nt_cleaned = dict()
        i = 0
        for row in resultSets[:-1]:
            triple = re.split(' ',row)
            if triple[2] in targets or triple[0] in targets:
                nt_cleaned[i] = triple
                i += 1
    except:
        #print (sys.exc_info())
        #logger.warning('Parsing inverse failed for %s' % target)
        nt_cleaned = False
    return nt_cleaned
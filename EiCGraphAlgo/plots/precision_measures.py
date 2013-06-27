'''
Created on Jun 26, 2013

@author: ldevocht
'''
from core.search import Searcher
from core.typeahead import prefix, dbPediaPrefix
from core.worker_pool import Worker
from core.resourceretriever import Resourceretriever
import random
import ujson

queries = [
            ["Germany","United States","Belgium"]#,
            #["ISWC 2008","Linked Data","Germany"]
           ]
searcher = Searcher()
worker = Worker()
resourceretriever = Resourceretriever()
iterations = 5

avps=[]

def handleResult(uri, target_uri, rankings):
    print('Looking for path between %s and %s' %(uri, target_uri))
    path = searcher.search(uri, target_uri, k=8)
    if path['path']:
        rank = len(path['path'])
        uris = rank/2
        even = uris % 2 == 0
        halved = False
        half = round(uris/2)
        
        s = 0
        
        for step in path['path']:
            if s not in rankings:
                rankings[s] = set()
            if 'node' in step['type']:
                print (step['uri'])
                print (s)
                #print (halved)
                #print (half)
                rankings[s].add(step['uri'])
                if s < half and not halved and not even:
                    s+=1
                elif s < half-1 and not halved and even:
                    s+=1
                elif s == half-1 and even:
                    halved = True
                elif s == half:
                    halved = True
                    s-=1
                elif even and halved:
                    even = False
                elif s >= half or halved:
                    s-=1
                else:
                    s-=1
                    
        print (rankings)
    
worker.createQueue(handleResult)
worker.startQueue(handleResult, 8)

for query in queries:
    uris = []
    paths = []
    rankings = {}
    
    for keyword in query:
        prefixes = dbPediaPrefix(keyword)
        pos = random.randrange(0,len(prefixes))
        uris.append(prefixes[pos]['uri'])
       
       
    #Iteration 1    
    for uri in uris:
        for target_uri in uris:
            if not (uri == target_uri):
                worker.queueFunction(handleResult, [uri, target_uri, rankings])
                #path = searcher.search(uri, target_uri, k=6)
                #print (path)
                #if path['path']:
                #    rank = len(path['path'])
                #    if rank not in rankings:
                #        rankings = set()
                #    rankings[rank] = path
                #    print (rankings)
    worker.waitforFunctionsFinish(handleResult)
    print("Done finding paths for iteration 1")
    
    #Iteration 2
    i = 2
    minRank = 0
    expanded = set()
    
    while (i < iterations):
        print ('Iteration %s' % i)
        minRank = min(rankings.keys())
        urisToExpand = rankings[minRank] - expanded
        if len(urisToExpand)==0:
            minRank=min(x for x in rankings.keys() if x > minRank)
            urisToExpand = rankings[minRank] - expanded
        for uri in urisToExpand:
            expanded.add(uri)
            print (uri)
            neighbours = resourceretriever.getResource(uri)
            if neighbours:
                for nb in neighbours:
                    neighbour = neighbours[nb]
                    subject = neighbour[0]
                    obj = neighbour[2]
                    pred = neighbour[1]
                    if subject.strip('<>') == uri.strip('<>'):
                        new_uri = obj
                    else:
                        new_uri = subject
                    if not (minRank+1) in rankings:
                        rankings[minRank+1] = set()
                    if '<' in new_uri and not 'XMLSchema' in new_uri and not 'category' in new_uri:
                        exists = False
                        for rank in rankings:
                            if new_uri.strip('<>') in rankings[rank]:
                                exists = rank
                        if not exists:
                            rankings[minRank+1].add(new_uri.strip('<>'))
                        else:
                            if exists > (minRank + 1):
                                rankings[minRank+1].add(new_uri.strip('<>'))
                                rankings[exists].remove(new_uri.strip('<>'))
                    
        print (rankings)
        i += 1
    print ('<--- Result for query:' % query)
    print (ujson.dumps(rankings))
    print ('--->')
    
    print ("Provide Relevancy scores")
    
    
    relevancies = {}
    
    # Dummy generation
    for rank in rankings:
        rankings[rank] = list(rankings[rank])
        relevancies[rank] = list()
        relevancies[rank] = [random.choice([i for i in range(2)]) for r in range(len(rankings[rank]))]
    print (ujson.dumps(relevancies))
    
    # Manualy define relevancies
    
    #relevancies = {"0":[0,1,0],
    #               "1":[1,0,1,0,1,1,1,0,0,0,0,0,1,0,1,1,0,1,1,1,0,1,1,0,0,0,1,0,1,1,1,0,1,1,0,1,1,0,1,0,0,0,0,0,1,1,1,0,1,0,1,1,0,1,1,0,0,0,0,1,0,0,1,1,0,1,1,1,0,0,1,1,1,1,0,1,0,0,1,1,0,1,0,0,0,0],
    #               "2":[1,1,0,1,0,0,1,0,1,0,0,0,0,1,1,0,0,0,0,1,0,1,0,0,0,0,1,0,0,0,1,0,1,0,1,0,1,1,0,0,0,0,1,1,1,0,1,1,0,0,1,0,1,0,1,0,1,1,0,1,1,0,0,1,1,0,0,1,1,1,0,0,0,0,1,1,0,1,0,0,0,0,1,0,1,1,1,0,0,0,1,1,0,0,1,1,1,0,0,1,0,0,1,1,1,1,0,0,1,0,1,0,0,0,0,1,0,1,1,0,0,1,0,0,1,0,1,0,0,1,1,1,0,1,1,1,0,0,1,0,0,1,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,0,1,1,1,0,0,0,0,1,1,0,1,0,1,0,1,0,1,1,1,1,0,1,0,0,1,0,0,0,0,0,0,0,1,0,1,1,1,0,0,0,1,1,1,1,1,1,1,0,1,0,0,1,1,1,1,1,1,1,0,1,0,0,0,0,1,0,0,1,0,0,0,0,0,0,1,0,1,0,1,1,0,1,0,0,1,1,0,0,1,0,1,1,1,1,0,0,1,1,1,1,0,1,0,1,0,0,1,0,0,1,1,1,0,0,0,1,0,0,0,1,1,1,1,1,1,0,0,0,0,0,0,1,0,1,1,0,0,0,0,1,0,0,0,0,1,0,1,0,1,1,0,0,0,0,1,0,0,1,0,1,1,1,1,0,0,1,1,0,1,0,0,1,0,1,1,1,0,0,0,0,1,1,0,0,1,0,1,0,1,0,1,1,0,0,1,0,0,1,0,1,0,1,0,1,1,0,1,1,1,1,0,0,0,0,1,1,0,0,0,0,1,1,1,0,1,1,1,0,1,1,0,0,1,1,1,1,1,0,0,0,0,1,0,1,1,0,0,1,0,1,1,1,1,1,0,1,1,0,1,1,1,1,0,1,0,1,0,1,1,1,0,0,0,1,1,1,1,1,0,0,0,0,1,1,1,1,0,0,0,1,0,1,0,0,1,1,0,0,0,0,1,1,1,1,0,1,0,0,1,1,0,1,1,1,1,1,0,0,0,0,0,1,1,0,1,1,1,1,0,0,1,0,1,0,1,0,0,0,0,1,0,1,1,0,0,1,0,1,0,1,1,1,1,0,1,0,0,0,1,0,1,1,1,1,0,0,1,0,0,0,1,0,1,1,1,0,1,0,1,1,0,1,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,1,1,1,0,1,1,1,0,1,1,0,0,0,1,1,0,0,1,0,1,0,1,1,1,0,1,0,0,0,0,1,0,1,0,1,1,1,1,1,0,1,0,0,0,1,1,1,1,1,0,0,1,0,1,0,1,1,1,0,0,0,1,1,1,0,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1,1,1,0,0,0,0,1,1,0,0,0,1,0,0,0,0,1,0,1,0,1,1,1,0,0,1,0,0,0,1,0,1,1,0,0,0,1,0,1,0,0,0,1,0,1,1,1,1,0,0,1,0,1,1,0,1,1,1,0,0,1,0,0,0,1,1,0,1,0,0,1,1,0,1,0,0,0,0,0,0,0,1,0,0,1,0,1,0,1,1,1,0,1,0,0,1,1,1,1,1,1,1,0,0,1,0,0,0,0,0,1,0,0,0,0,1,1,0,0,0,1,0,1,1,1,1,1,1,1,1,0,0,1,0,0,1,0,0,1,1,0,0,1,1,0,1,1,1,0,1,0,1,1,0,0,0,1,1,0,0,1,0,0,0,1,1,0,0,0,1,1,1,0,1,0,0,0,1,1,1,0,0,1,1,0,0,0,0,0,1,0,1,0,1,1,1]
    #                }

    
    print('Precision')
    
    precision = {}
    rels = {}
    relevant = 0
    
    for rank in relevancies:
        precision[rank] = 0
        retrieved = len(relevancies[rank])
        j = 0
        for rel in relevancies[rank]:
            if rel == 1:
                j += 1
                relevant += 1
        precision[rank] = j / len(relevancies[rank])
        rels[rank] = j
        
    print (precision)     

    print ('Average Precision')
    avp = 0
    for rank in precision:
        avp += precision[rank] * rels[rank]
        
    avp = avp / relevant
    avps.append(avp)

print (avps)
print ('DONE')
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
            #["Germany","United States","Belgium"],
            ["LDOW","Christian Bizer"],
            ["ISWC2012","Lyon", "France"],
            ["ISWC2008","Linked Data","Germany"],
            ["Linked Data","WWW2012"],
            ["Selver Softic", "Semantic Web", "Michael Hausenblas"],
            ["Selver Softic", "Linked Data", "Information Retrieval"],
            ["Laurens De Vocht", "Selver Softic"],
            ["Laurens De Vocht", "Selver Softic", "2011"],
            ["Laurens De Vocht", "Linked Data", "WWW2013"],
            ["Chris Bizer", "WWW2013", "ISWC2010"],
            #
           ]
searcher = Searcher()
worker = Worker()
resourceretriever = Resourceretriever()
iterations = 6
results = []

avps=[]

f = open('results.json','w')

def handleResult(uri, target_uri, rankings):
    print('Looking for path between %s and %s' %(uri, target_uri))
    path = searcher.search(uri, target_uri, k=8)
    if path['path']:
        rank = len(path['path'])
        uris = (rank+1)/2
        even = uris % 2 == 0
        halved = False
        half = round(uris/2)
        
        s = 0
        
        for step in path['path']:
            t = min(s,uris-1-s)
            if t not in rankings:
                rankings[t] = set()
            if 'node' in step['type']:
                print (step['uri'])
                print (uris-1)
                print (t)
                rankings[t].add(step['uri'])
                s+=1
                    
        print (rankings)

for query in queries:
    uris = []
    paths = []
    rankings = {}
    worker.createQueue(handleResult)
    worker.startQueue(handleResult, 8)

    for keyword in query:
        prefixes = prefix(keyword)
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

    expanded = set()
    minRank = 0
    while (i < iterations):
        print ('Iteration %s' % i)
        urisToExpand = rankings[minRank] - expanded
        if len(urisToExpand)==0:
            print ('no uris to expand in rank %s' % minRank)
            minRank=min(x for x in rankings.keys() if x > minRank)
            print ('new minRank %s' % minRank)
            urisToExpand = rankings[minRank] - expanded
        for uri in urisToExpand:
            expanded.add(uri)
            print (len(expanded))
            print (minRank)
            print (uri)
            neighbours = resourceretriever.getResource(uri)
            if neighbours:
                p = 0;
                for nb in neighbours:
                    if p < 5:
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
                                if new_uri.strip('<>') in rankings[rank] or new_uri.strip('<>') == rankings[rank]:
                                    exists = rank
                            if not exists:
                                rankings[minRank+1].add(new_uri.strip('<>'))
                            else:
                                if exists > (minRank + 1):
                                    rankings[minRank+1].add(new_uri.strip('<>'))
                                    rankings[exists].remove(new_uri.strip('<>'))
                    p += 1
                    
        print (rankings)
        i += 1
    print ('<--- Result for query:' % query)
    print (ujson.dumps(rankings))
    results.append(ujson.dumps(rankings))
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
    print (avp)
    avps.append(avp)

print (avps)
print ('DONE')
f.write(ujson.dumps(results))
f.close()
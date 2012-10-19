from sindice import search
import pickle
import ujson

sources = ['http://dbpedia.org/resource/David_Guetta']

destinations = ['http://dbpedia.org/resource/France',
                'http://dbpedia.org/resource/New_York',
                'http://dbpedia.org/resource/United_States_of_America',
                'http://dbpedia.org/resource/Paris',
                'http://dbpedia.org/resource/Jimi_Hendrix',
                'http://dbpedia.org/resource/Elvis_Presley',
                ]

for s in sources:
    for d in destinations:
        print ("Calculation for {0} to {1}".format(s,d)) 
        r = dict()
        r = search.search(d,s)
        r['source'] =  s
        r['destination'] = d
        print("Execution time: %s" % str(r['execution_time']))
        pickle.dump(r,open( "cached_paths/%s.dump" % hash('{0}_{1}'.format(s,d)), "wb" ))
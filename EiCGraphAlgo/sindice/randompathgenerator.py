from sindice import search
import pickle
import ujson
import numpy as np

sources = [
           'http://dbpedia.org/resource/David_Guetta',
           'http://dbpedia.org/resource/Germany',
           'http://dbpedia.org/resource/Spain',
           'http://dbpedia.org/resource/China',
           'http://dbpedia.org/resource/San_Francisco',
           'http://dbpedia.org/resource/Rio_de_Janeiro',
           'http://dbpedia.org/resource/Avril_Lavigne',
           'http://dbpedia.org/resource/Dolly_Parton',
           'http://dbpedia.org/resource/Giuseppe_Verdi',
           'http://dbpedia.org/resource/Joan_Baez',
           'http://dbpedia.org/resource/Rihanna',
           'http://dbpedia.org/resource/James_Brown',
           'http://dbpedia.org/resource/Jimmy_Page',
           'http://dbpedia.org/resource/Igor_Stravinsky',
           'http://dbpedia.org/resource/Kanye_West',
           'http://dbpedia.org/resource/Stevie_Wonder',
           'http://dbpedia.org/resource/Mike_Oldfield',
           'http://dbpedia.org/resource/Kurt_Cobain',
           'http://dbpedia.org/resource/Henry_Mancini',
           'http://dbpedia.org/resource/Alice_Cooper',
           'http://dbpedia.org/resource/Ozzy_Osbourne',
           'http://dbpedia.org/resource/Tina_Turner',
           'http://dbpedia.org/resource/Louis_Armstrong',
           'http://dbpedia.org/resource/Brian_May',
           'http://dbpedia.org/resource/Georges_Brassens',
           'http://dbpedia.org/resource/Nelly_Furtado',            
        ]

destinations = ['http://dbpedia.org/resource/New_York',
                'http://dbpedia.org/resource/Paris',
                'http://dbpedia.org/resource/Germany',
                'http://dbpedia.org/resource/Chile',
                'http://dbpedia.org/resource/India',
                'http://dbpedia.org/resource/Brazil',
                'http://dbpedia.org/resource/Iran',
                'http://dbpedia.org/resource/Italy',
                'http://dbpedia.org/resource/Japan',
                'http://dbpedia.org/resource/Netherlands',
                'http://dbpedia.org/resource/Chicago',
                'http://dbpedia.org/resource/Hungary',
                'http://dbpedia.org/resource/London',
                'http://dbpedia.org/resource/Los_Angeles',
                'http://dbpedia.org/resource/Belgium',
                'http://dbpedia.org/resource/Algeria',
                'http://dbpedia.org/resource/Lisbon',
                'http://dbpedia.org/resource/Greece',
                'http://dbpedia.org/resource/Iceland',
                'http://dbpedia.org/resource/Bulgaria',
                'http://dbpedia.org/resource/Colombia',
                'http://dbpedia.org/resource/California',
                'http://dbpedia.org/resource/Morocco',
                'http://dbpedia.org/resource/Berlin',
                'http://dbpedia.org/resource/Norway',
                'http://dbpedia.org/resource/Moscow',
                'http://dbpedia.org/resource/European_Union',
                'http://dbpedia.org/resource/Finland',
                'http://dbpedia.org/resource/Europe',
                'http://dbpedia.org/resource/Republic_of_Ireland',
                'http://dbpedia.org/resource/Barcelona',
                'http://dbpedia.org/resource/Croatia',
                'http://dbpedia.org/resource/England',
                'http://dbpedia.org/resource/Kazakhstan',
                'http://dbpedia.org/resource/Amsterdam',
                'http://dbpedia.org/resource/Athens',
                'http://dbpedia.org/resource/Cairo',
                'http://dbpedia.org/resource/Cleveland',
                'http://dbpedia.org/resource/Burma',
                'http://dbpedia.org/resource/Alaska'
                ]

def randomSourceAndDestination():
    response = dict()
    random_source = np.random.randint(len(sources))
    random_dest = np.random.randint(len(destinations))
    response['source'] = sources[random_source]
    response['destination'] = destinations[random_dest]
    return response

def generateCachedPaths():
    for s in sources:
        for d in destinations:
            print ("Calculation for {0} to {1}".format(s,d)) 
            r = dict()
            try:
                r = search.search(s,d)
                r['source'] =  s
                r['destination'] = d
                print("Execution time: %s" % str(r['execution_time']))
                pickle.dump(r,open( "cached_paths/%s.dump" % hash('{0}_{1}'.format(s,d)), "wb" ))
            except:
                print("Could not find path between {0} and {1}".format(s,d))
                
#generateCachedPaths()
            
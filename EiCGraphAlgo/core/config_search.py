#Define properties to ignore:
blacklist = frozenset([
             "<http://dbpedia.org/ontology/wikiPageWikiLink>",
             "<http://dbpedia.org/property/title>",
             "<http://dbpedia.org/ontology/abstract>",
             #"<http://xmlns.com/foaf/0.1/page>",
             "<http://dbpedia.org/property/wikiPageUsesTemplate>",
             "<http://dbpedia.org/ontology/wikiPageExternalLink>",
             #"<http://dbpedia.org/ontology/wikiPageRedirects>",
             "<http://purl.org/muto/core#tagMeans>",
             "<http://dbpedia.org/ontology/wikiPageDisambiguates>",
             "<http://dbpedia.org/ontology/governmentType>",
             "<http://dbpedia.org/ontology/officialLanguage>",
             "<http://dbpedia.org/ontology/spokenIn>",
             "<http://dbpedia.org/ontology/language>",
             "<http://purl.org/dc/elements/1.1/description>",
             "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>",
             #"<http://www.w3.org/2002/07/owl#sameAs>",
             "<http://purl.org/dc/terms/subject>",
             #"<http://dbpedia.org/property/website>",
             "<http://dbpedia.org/property/label>",
             #"<http://xmlns.com/foaf/0.1/homepage>",
             "<http://dbpedia.org/ontology/wikiPageDisambiguates>",
             "<http://dbpedia.org/ontology/thumbnail>",
             "<http://xmlns.com/foaf/0.1/depiction>",
             "<http://dbpedia.org/ontology/type>",
             "<http://dbpedia.org/ontology/related>",
             "<http://dbpedia.org/ontology/populationPlace>",
             "<http://dbpedia.org/ontology/timeZone>",
             ])

valid_domains = frozenset([
                        "dbpedia",
                        "freebase",
                        "colinda",
                        "dblp",
                        "localhost"
			])
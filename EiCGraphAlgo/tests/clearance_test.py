import random
import unittest
from core import search,typeahead,resourceretriever_async
from core.typeahead import TypeAhead

class TestBasicFunctions(unittest.TestCase):

    def setUp(self):
        self.searcher = search.Searcher()
        self.resourceretriever = resourceretriever_async.Resourceretriever()
        self.th = typeahead.TypeAhead()

    def test_search(self):
        good = self.searcher.search('http://dbpedia.org/resource/Brussels','http://dbpedia.org/resource/Ireland')
        res = len(good['path']) > 0
        self.assertTrue(res)

        # should return a path false for a typo
        #bad = self.searcher.search('http://dbpedia.org/resource/Brussfels','http://dbpedia.org/resource/Ireland')
        #self.assertFalse(bad['path'])

    def test_typeahead(self):
        self.assertTrue(len(self.th.prefix("WWW"))>0)

    def test_describe(self):
        self.assertTrue('label' in self.resourceretriever.describeResource('http://dbpedia.org/resource/Brussels'))

if __name__ == '__main__':
    unittest.main()
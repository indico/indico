from MaKaC.common.cache import MultiLevelCache, MultiLevelCacheEntry

class SECacheEntry(MultiLevelCacheEntry):
    def __init__(self, websession, query):
        MultiLevelCacheEntry.__init__(self)

        self._data = {}
        self._websession = websession
        self._query = query

    def getData(self):        
        return self._data
        
    def getWebSession(self):
        return self._websession

    def getQuery(self):
        return self._query
        
    def setPage(self, page, record):
        self._data[page] = record



class SECache(MultiLevelCache):
    """ Cache that stores the appropriate record numbers for a specific search query,
    in order to allow users to browse search results """
    
    def __init__(self):
        MultiLevelCache.__init__(self, 'search')

    def _generateFileName(self, id, version):
        return '%s_%s' % (id, version)

    def _generatePath(self, obj):
        """ Generate the actual hierarchical location """

        # websess: 12345 query: abcd -> /cachedir/1/12345/abcd

        return [obj.getWebSession()]

    def loadObject(self, fnList):
        """ Load an object from the cache"""
        return MultiLevelCache.loadObject(self, fnList)

    def cacheObject(self, object, version):
        """ Caches an object """

        path = self._generatePath(object);
        fileName = self._generateFileName(object.getQuery(), version)
        
        MultiLevelCache.cacheObject(self, path, fileName, object)

    def isDirty(self, path, object):
        """ TODO: implement this one (websession date?) """
        return False


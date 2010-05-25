from MaKaC.common.cache import MultiLevelCache, MultiLevelCacheEntry

class SECacheEntry(MultiLevelCacheEntry):
    def __init__(self, websession, query):
        MultiLevelCacheEntry.__init__(self)
        self._websession = websession
        self._query = query

    def getWebSession(self):
        return self._websession

    def getQuery(self):
        return self._query

    def setPage(self, page, record):
        self._data[page] = record

    @classmethod
    def create(cls, content, websession, query):
        entry = cls(websession, query)
        entry.setContent(content)
        return entry



class SECache(MultiLevelCache):
    """
    Cache that stores the appropriate record numbers for a specific search query,
    in order to allow users to browse search results
    """

    _entryFactory = SECacheEntry

    def __init__(self):
        MultiLevelCache.__init__(self, 'search')

    def _generateFileName(self, entry, version):
        return '%s_%s' % (entry.getQuery(), version)

    def _generatePath(self, entry):
        """ Generate the actual hierarchical location """

        # websess: 12345 query: abcd -> /cachedir/1/12345/abcd

        return [entry.getWebSession()]

    def isDirty(self, path, object):
        """ TODO: implement this one (websession date?) """
        return False


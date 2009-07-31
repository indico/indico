import getopt, sys

from MaKaC.common.db import DBMgr
from MaKaC.common.xmlGen import XMLGen
from MaKaC.export.oai2 import OAIResponse, DataInt, PrivateDataInt

from base import prettyPrint

class FakeOAIResponse(OAIResponse):

    def __init__(self, host, url, private):
        OAIResponse.__init__(self, host, url, private)
        self._token = None

    def getToken(self):
        return self._token

    def isEnd(self):
        return self._end

    def print_record(self, record, format):
        self._token = None
        if self._DataInt.isDeletedItem(self._DataInt.objToId(record)):
            print '- %s' % prettyPrint(record)
        else:
            print '+ %s' % prettyPrint(record)

    def OAICacheIn(self, resumptionToken, sysnos):
        OAIResponse.OAICacheIn(self, resumptionToken, sysnos)
        self._token = resumptionToken


def fetchOAI(private, fromDate, untilDate):
    dbi = DBMgr.getInstance()
    dbi.startRequest()

    response = FakeOAIResponse('host','/oai.py',private)


    response.OAIListRecords(fromDate,untilDate,None,'marcxml', None)
    token = response.getToken()

    while not token == None:
        response.OAIListRecords(fromDate,untilDate,None,'marcxml', token)
        token = response.getToken()

    dbi.endRequest()

def process(options):

    private, fromDate, untilDate = False, None, None

    for o,v in options:
        if o == '--private':
            private = True
        elif o == '--from':
            fromDate = v
        elif o == '--until':
            untilDate = v

    fetchOAI(private, fromDate, untilDate)


if __name__ == '__main__':
    parsedOpt, rest = getopt.getopt(sys.argv[1:], '', ["private","from=","until="])

    process(parsedOpt)

    if len(rest) > 0:
        print "Unrecognized: %s" % rest
        sys.exit(-1)

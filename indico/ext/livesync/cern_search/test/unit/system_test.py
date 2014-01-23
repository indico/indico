# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

"""
System tests for indico.ext.livesync.invenio

Here, uploads are  tested agains a phony Invenio server
"""

# standard lib imports
import cgi
import BaseHTTPServer
from StringIO import StringIO
from threading import Thread


# dependency imports
from lxml import etree

from indico.tests.python.unit.util import IndicoTestCase

# plugin imports
from indico.ext.livesync.cern_search import CERNSearchUploadAgent
from indico.ext.livesync.test.unit.base import _TUpload


class FakeHTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    """
    "Fake" Invenio server
    """

    def do_GET(self):
        self.wfile.write('sorry, only POST is allowed')

    def do_POST(self):

        contType, params = cgi.parse_header(
            self.headers.getheader('content-type'))
        if contType == 'multipart/form-data':
            varsDict = cgi.parse_multipart(self.rfile, params)
        elif contType == 'application/x-www-form-urlencoded':
            length = int(self.headers.getheader('content-length'))
            varsDict = cgi.parse_qs(self.rfile.read(length),
                                    keep_blank_values=1)
        else:
            varsDict = {}

        try:
            xmlDoc = etree.parse(StringIO(varsDict['xml'][0]))

            ns = {'marc': 'http://www.loc.gov/MARC21/slim'}

            # get just the ids
            records = xmlDoc.xpath('/marc:collection/marc:record',
                            namespaces=ns)

            # build a "record" from the XML
            for recNode in records:
                rid = recNode.xpath(
                    './marc:datafield[@tag="970"]/marc:subfield/text()',
                    namespaces=ns)[0]
                deleted = recNode.xpath('./marc:datafield[@tag="980"]/marc:subfield/text()',
                                        namespaces=ns)[0] == 'DELETED'
                title = recNode.xpath(
                    './marc:datafield[@tag="245"]/marc:subfield/text()',
                    namespaces=ns)
                title = title[0] if title else None

                self.server.recordSet[rid] = {'title': title, 'deleted': deleted}

            self.wfile.write('')
        except Exception, e:
            self.server.recordSet = None
            self.server.exception = sys.exc_info()


        # TODO: Handle deleted!


class FakeCERNSearch(Thread):

    def __init__(self, host, port, recordSet):
        super(FakeCERNSearch, self).__init__()
        self._server = BaseHTTPServer.HTTPServer((host, port), FakeHTTPHandler)
        self._server.recordSet = recordSet
        self._server.exception = None

    def shutdown(self):
        self._server.shutdown()

    def run(self):
        try:
            self._server.serve_forever()
        finally:
            # always close the server
            self._server.server_close()

    @property
    def exception(self):
        return self._server.exception


class TestUpload(_TUpload, IndicoTestCase):
    _server = FakeCERNSearch
    _agent = CERNSearchUploadAgent

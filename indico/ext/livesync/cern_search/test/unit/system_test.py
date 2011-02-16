# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

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

# plugin imports
from indico.ext.livesync.cern_search import CERNSearchUploadAgent
from indico.ext.livesync.bistate.test.unit import _TestUpload


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
            title = recNode.xpath(
                './marc:datafield[@tag="245"]/marc:subfield/text()',
                namespaces=ns)[0]

            self.server.recordSet[rid] = {'title': title}

        self.wfile.write('')

        # TODO: Handle deleted!


class FakeCERNSearch(Thread):

    def __init__(self, host, port, recordSet):
        super(FakeCERNSearch, self).__init__()
        self._server = BaseHTTPServer.HTTPServer((host, port), FakeHTTPHandler)
        self._server.recordSet = recordSet

    def shutdown(self):
        self._server.shutdown()

    def run(self):
        try:
            self._server.serve_forever()
        finally:
            # always close the server
            self._server.server_close()


class TestUpload(_TestUpload):
    _server = FakeCERNSearch
    _agent = CERNSearchUploadAgent

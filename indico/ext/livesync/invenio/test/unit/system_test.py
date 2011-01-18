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
import cgi, contextlib, time
import BaseHTTPServer
from StringIO import StringIO
from threading import Thread


# dependency imports
import dateutil
from lxml import etree

# indico imports
from indico.tests.python.unit.util import IndicoTestCase

# plugin imports
from indico.ext.livesync.invenio.agent import InvenioBatchUploaderAgent
from indico.ext.livesync.tasks import LiveSyncUpdateTask
from indico.ext.livesync.test.unit.base import LiveSync_Feature

FAKE_SERVICE_PORT = 12380
globalRecordSet = dict()


class FakeHTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    """
    "Fake" Invenio server
    """

    def do_GET(self):
        self.wfile.write('sorry, only POST is allowed')

    def do_POST(self):
        global globalRecordSet

        contType, params = cgi.parse_header(
            self.headers.getheader('content-type'))
        if contType == 'multipart/form-data':
            varsDict = cgi.parse_multipart(self.rfile, params)
        elif contType == 'application/x-www-form-urlencoded':
            length = int(self.headers.getheader('content-length'))
            varsDict = cgi.parse_qs(
                self.rfile.read(length), keep_blank_values=1)
        else:
            varsDict = {}

        xmlDoc = etree.parse(StringIO(varsDict['file'][0]))

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

            globalRecordSet[rid] = {'title': title}

        self.wfile.write('[INFO] blablablabla uploaded_file.xml')


class FakeInvenio(Thread):

    def __init__(self, host, port):
        super(FakeInvenio, self).__init__()
        self._server = BaseHTTPServer.HTTPServer((host, port), FakeHTTPHandler)

    def shutdown(self):
        self._server.shutdown()

    def run(self):
        try:
            self._server.serve_forever()
        finally:
            # always close the server
            self._server.server_close()


class TestUpload(IndicoTestCase):

    _requires = ['db.DummyUser', LiveSync_Feature, 'util.RequestEnvironment']

    def tearDown(self):
        super(TestUpload, self).tearDown()
        self._closeEnvironment()

    @contextlib.contextmanager
    def _generateTestResult(self):

        global globalRecordSet, FAKE_SERVICE_PORT

        fakeInvenio = FakeInvenio('', FAKE_SERVICE_PORT)

        agent = InvenioBatchUploaderAgent('test1', 'test1', 'test',
                                          0, 'http://localhost:%s' % \
                                          FAKE_SERVICE_PORT)

        globalRecordSet = dict()

        with self._context('database', 'request'):
            self._sm.registerNewAgent(agent)
            agent.preActivate(0)
            agent.setActive(True)
            # execute code
            yield

        time.sleep(1)

        fakeInvenio.start()

        # params won't be used
        task = LiveSyncUpdateTask(dateutil.rrule.MINUTELY)

        try:
            task.run()
        finally:
            fakeInvenio.shutdown()
            fakeInvenio.join()

            # can't reuse the same port, as the OS won't have it free
            FAKE_SERVICE_PORT += 1

    def testSmallUpload(self):
        """
        Tests uploading multiple records (small)
        """
        with self._generateTestResult():
            conf1 = self._home.newConference(self._dummy)
            conf1.setTitle('Test Conference 1')
            conf2 = self._home.newConference(self._dummy)
            conf2.setTitle('Test Conference 2')

        self.assertEqual(
            globalRecordSet,
            {
                'INDICO.0': {'title': 'Test Conference 1'},
                'INDICO.1': {'title': 'Test Conference 2'}
                })

    def testLargeUpload(self):
        """
        Tests uploading multiple records (large)
        """
        with self._generateTestResult():
            for nconf in range(0, 100):
                conf = self._home.newConference(self._dummy)
                conf.setTitle('Test Conference %s' % nconf)

        self.assertEqual(
            globalRecordSet,
            dict(('INDICO.%s' % nconf,
                  {'title': 'Test Conference %s' % nconf}) \
                 for nconf in range(0, 100)))



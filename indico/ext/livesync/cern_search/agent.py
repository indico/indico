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
Agent definitions for CERN Search
"""

# standard library imports
import time, base64
from urllib2 import urlopen, Request, HTTPError
from urllib import urlencode

# dependency imports
from lxml import etree

# plugin imports
from indico.ext.livesync.agent import AgentProviderComponent, RecordUploader
from indico.ext.livesync.bistate import BistateBatchUploaderAgent

from indico.util.date_time import nowutc


class CERNSearchUploadAgent(BistateBatchUploaderAgent):

    _extraOptions = {'url': 'Server URL',
                     'username': 'Username',
                     'password': 'Password'}

    def __init__(self, aid, name, description, updateTime,
                 access=None, url=None, username=None, password=None):
        super(CERNSearchUploadAgent, self).__init__(
            aid, name, description, updateTime, access)
        self._url = url
        self._username = username
        self._password = password

    def _run(self, records, logger=None, monitor=None, dbi=None, task=None):

        self._v_logger = logger

        # the uploader will manage everything for us...
        uploader = CERNSearchRecordUploader(logger, self, self._url,
                                            self._username, self._password, task)
        if self._v_logger:
            self._v_logger.info('Starting metadata/upload cycle')

        # iterate over the returned records and upload them
        return uploader.iterateOver(records, dbi=dbi)


class CERNSearchRecordUploader(RecordUploader):
    """
    A worker that uploads data using HTTP
    """

    def __init__(self, logger, agent, url, username, password, task=None):
        super(CERNSearchRecordUploader, self).__init__(logger, agent)
        self._url = url
        self._username = username
        self._password = password
        self._task = task

    def _postRequest(self, batch):

        pass

    def _uploadBatch(self, batch):
        """
        Uploads a batch to the server
        """

        url = "%s/ImportXML" % self._url

        self._logger.debug('getting a batch')

        tstart = time.time()
        # get a batch

        self._logger.info('Generating metadata')
        data = self._agent._getMetadata(batch, logger=self._logger)
        self._logger.info('Metadata ready ')

        postData = {
            'xml': data
            }

        tgen = time.time() - tstart

        req = Request(url)
        # remove line break
        cred = base64.encodestring(
            '%s:%s' % (self._username, self._password)).strip()

        req.add_header("Authorization", "Basic %s" % cred)

        try:
            result = urlopen(req, data=urlencode(postData))
        except HTTPError, e:
            self._logger.exception("Status %s: \n %s" % (e.code, e.read()))
            raise Exception('upload failed')

        result_data = result.read()

        tupload = time.time() - (tstart + tgen)

        self._logger.debug('rec %s result: %s' % (batch, result_data))

        xmlDoc = etree.fromstring(result_data)

        # right now there is nothing else to pay attention to
        booleanResult = etree.tostring(xmlDoc, method="text")

        if self._task:
            self._task.setOnRunningListSince(nowutc())

        if result.code == 200 and booleanResult == 'true':
            self._logger.info('Batch of %d records stored in server'
                              ' [%f s %f s]' % \
                              (len(batch), tgen, tupload))
        else:
            self._logger.error('Records: %s output: %s '
                               '(HTTP code %s)' % (batch, result_data, result.code))
            raise Exception('upload failed')

        return True


class CERNSearchAgentProviderComponent(AgentProviderComponent):
    _agentType = CERNSearchUploadAgent

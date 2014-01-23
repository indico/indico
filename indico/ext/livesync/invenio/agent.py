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

# standard lib imports
import time

# plugin imports
from indico.ext.livesync.agent import AgentProviderComponent, RecordUploader
from indico.ext.livesync.bistate import BistateBatchUploaderAgent
from indico.ext.livesync.invenio.invenio_connector import InvenioConnector
from indico.util.date_time import nowutc


class InvenioBatchUploaderAgent(BistateBatchUploaderAgent):

    def _run(self, records, logger=None, monitor=None, dbi=None, task=None):

        self._v_logger = logger

        server = InvenioConnector(self._url)

        # the uploader will manage everything for us...

        uploader = InvenioRecordUploader(logger, self, server, task)

        if self._v_logger:
            self._v_logger.info('Starting metadata/upload cycle')

        # iterate over the returned records and upload them
        return uploader.iterateOver(records, dbi=dbi)


class InvenioRecordUploader(RecordUploader):
    """
    A worker that uploads data using HTTP
    """

    def __init__(self, logger, agent, server, task=None):
        super(InvenioRecordUploader, self).__init__(logger, agent)
        self._server = server
        self._task = task

    def _uploadBatch(self, batch):
        """
        Uploads a batch to the server
        """

        self._logger.debug('getting a batch')

        tstart = time.time()
        # get a batch

        self._logger.info('Generating metadata')
        data = self._agent._getMetadata(batch, logger=self._logger)
        self._logger.info('Metadata ready ')

        tgen = time.time() - tstart
        try:
            result = self._server.upload_marcxml(data, "-ir").read()
        except Exception:
            self._logger.exception("Failed uploading records to local invenio server")
            raise

        tupload = time.time() - (tstart + tgen)

        if self._task:
            self._task.setOnRunningListSince(nowutc())

        self._logger.debug('rec %s result: %s' % (batch, result))

        if isinstance(result, long):
            self._logger.info('Batch of %d records submitted (task %s)'
                              '[%f s %f s]' % (len(batch), result, tgen, tupload))

        elif result.startswith('[INFO]'):
            fpath = result.strip().split(' ')[-1]
            self._logger.info('Batch of %d records stored in server (%s) '
                              '[%f s %f s]' % \
                              (len(batch), fpath, tgen, tupload))
        else:
            self._logger.error('Records: %s output: %s' % (batch, result))
            raise Exception('upload failed')

        return True


class InvenioAgentProviderComponent(AgentProviderComponent):
    _agentType = InvenioBatchUploaderAgent

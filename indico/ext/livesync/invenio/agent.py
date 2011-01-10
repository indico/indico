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

# standard lib imports
from threading import Thread
from Queue import Queue, Empty
import time, transaction

# plugin imports
from indico.ext.livesync.agent import PushSyncAgent, AgentProviderComponent
from indico.ext.livesync.invenio.invenio_connector import InvenioConnector

# legacy indico
from MaKaC import conference
from MaKaC.common import DBMgr

# legacy OAI/XML libs - this should be replaced soon
from MaKaC.export.oai2 import DataInt
from MaKaC.common.xmlGen import XMLGen

# some useful constants
STATUS_DELETED, STATUS_CREATED, STATUS_CHANGED = 1, 2, 4


class UploaderSlave(Thread):
    """
    A worker, that uploads data using HTTP
    """
    def __init__(self, name, server, queue, logger):
        self._server = server
        self._keepRunning = True
        self._logger = logger
        self._terminate = False
        self.result = True
        self._queue = queue
        self._name = name

        super(UploaderSlave, self).__init__(name=name)

    def run(self):

        DBMgr.getInstance().startRequest()

        self._logger.debug('Worker [%s] started' % self._name)
        try:
            while True:
                taskFetched = False
                try:
                    batch = self._queue.get(True, 2)
                    taskFetched = True
                    self.result &= self._processBatch(batch)
                except Empty:
                    pass
                finally:
                    if taskFetched:
                        self._queue.task_done()

                if self._terminate:
                    break
        except:
            self._logger.exception('Worker [%s]:' % self._name)
            return 1
        finally:
            DBMgr.getInstance().endRequest()
            self._logger.debug('Worker [%s] finished' % self._name)
        self._logger.debug('Worker [%s] returning %s' % (self._name, self.result))

    def terminate(self):
        """
        This function is executed on the parent side
        """
        self._terminate = True

    def _processBatch(self, batch):

        self._logger.debug('getting a batch')
        # get a batch

        data = self._getMetadata(batch)

        result = self._server.upload_marcxml(data, "-ir").read()

        self._logger.debug('rec %s result: %s' % (batch, result))

        if result.startswith('[INFO]'):
            fpath = result.strip().split(' ')[-1]
            self._logger.info('record set %s stored in server (%s)' % \
                              (batch, fpath))
        else:
            self._logger.error('rec %s output: %s' % (batch, result))
            raise Exception('upload failed')

        return True

    def _getMetadata(self, records):
        """
        Retrieves the metadata for the record
        """
        xg = XMLGen()
        di = DataInt(xg)

        xg.initXml()

        xg.openTag("collection", [["xmlns", "http://www.loc.gov/MARC21/slim"]])

        for operation, record in records:
            di.toMarc(record, overrideCache=True,
                      deleted=(operation & STATUS_DELETED))

        xg.closeTag("collection")

        return xg.getXml()


class InvenioRecordProcessor(object):

    @classmethod
    def _setStatus(cls, chgSet, obj, state):
        if obj not in chgSet:
            chgSet[obj] = 0

        chgSet[obj] |= state

    @classmethod
    def _breakDownCategory(cls, categ, chgSet, state):

        # categories are never converted to records

        for conf in categ.getAllConferenceList():
            cls._breakDownConference(conf, chgSet, state)

    @classmethod
    def _breakDownConference(cls, conf, chgSet, state):

        cls._setStatus(chgSet, conf, state)

        for contrib in conf.getContributionList():
            cls._breakDownContribution(contrib, chgSet, state)

    @classmethod
    def _breakDownContribution(cls, contrib, chgSet, state):

        cls._setStatus(chgSet, contrib, state)

        for scontrib in contrib.getSubContributionList():
            cls._setStatus(chgSet, scontrib, state)

    @classmethod
    def _computeProtectionChanges(cls, obj, action, chgSet):
        if isinstance(obj, conference.Category):
            cls._breakDownCategory(obj, chgSet, STATUS_CHANGED)
        elif isinstance(obj, conference.Conference):
            cls._breakDownConference(obj, chgSet, STATUS_CHANGED)
        elif isinstance(obj, conference.Contribution):
            cls._breakDownContribution(obj, chgSet, STATUS_CHANGED)
        elif isinstance(obj, conference.SubContribution):
            cls._setStatus(chgSet, obj, STATUS_CHANGED)

    @classmethod
    def computeRecords(cls, data):
        """
        Receives a sequence of ActionWrappers and returns a sequence
        of records to be updated (created, changed or deleted)
        """

        records = dict()

        for __, aw in data:
            obj = aw.getObject()

            if obj in records:
                # seen before? jump over this one
                continue
            else:
                records[obj] = 0

            for action in aw.getActions():

                if action == 'deleted':
                    # if the record has been deleted, mark it as such
                    # nothing else will matter
                    records[obj] |= STATUS_DELETED

                elif action == 'created':
                    # if the record has been created, mark it as such
                    records[obj] |= STATUS_CREATED

                elif action in ['data_changed', 'acl_changed', 'moved']:
                    # categories are ignored
                    records[obj] |= STATUS_CHANGED

                elif action in ['set_private', 'set_public']:
                    # protection changes have to be handled more carefully
                    cls._computeProtectionChanges(obj, action, records)

        for record, state in records.iteritems():
            yield record, state


class InvenioBatchUploaderAgent(PushSyncAgent):
    """
    Invenio WebUpload-compatible LiveSync agent
    """

    BATCH_SIZE, NUM_WORKERS = 500, 2

    _extraOptions = {'url': 'Server URL'}

    def __init__(self, aid, name, description, updateTime, url=None):
        super(InvenioBatchUploaderAgent, self).__init__(
            aid, name, description, updateTime)
        self._url = url

    def _prepareQueue(self):
        """
        Prepares the queue that will be used in memory, for the slave
        processes. Since it is volatile, it is not saved in the DB.
        """
        self._v_queue = Queue()

    def _run(self, manager, data, lastTS):

        success = True
        workers = {}
        server = InvenioConnector(self._url)

        # prepare volatile attributes
        self._prepareQueue()

        # take operations and choose which records to send

        for i in range(0, InvenioBatchUploaderAgent.NUM_WORKERS):
            workers[i] = UploaderSlave("Uploader%s" % i, server,
                                       self._v_queue,
                                       self._v_logger)
            workers[i].start()

        currentBatch = []

        self._v_logger.info('Starting metadata/upload cycle')

        for record, operation in InvenioRecordProcessor.computeRecords(data):
            if isinstance(record, conference.Category):
                continue

            # when BATCH_SIZE is passed, enqueue it
            if len(currentBatch) > (InvenioBatchUploaderAgent.BATCH_SIZE - 1):
                self._v_queue.put(currentBatch)
                currentBatch = []

            currentBatch.append((operation, record))

        # if there is an incomplete batch remaining, add it
        if currentBatch:
            self._v_queue.put(currentBatch)

        self._v_logger.debug('joining queue')

        self._v_queue.join()

        self._v_logger.debug('joining workers')

        for worker in workers.values():
            worker.terminate()
            worker.join()
            success &= (not worker.is_alive() and worker.result)

        self._v_logger.debug('done!')
        return lastTS if success else None


# Attention: if this class is not declared, the LiveSync management interface
# will never know this plugin exists!

class InvenioAgentProviderComponent(AgentProviderComponent):
    _agentType = InvenioBatchUploaderAgent

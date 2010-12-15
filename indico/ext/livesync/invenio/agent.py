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


from indico.ext.livesync.agent import PushSyncAgent, AgentExecutionException, \
     AgentProviderComponent
from indico.ext.livesync.invenio.invenio_connector import InvenioConnector

# legacy indico
from MaKaC import conference

# legacy OAI/XML libs - this should be replaced soon
from MaKaC.export.oai2 import DataInt
from MaKaC.common.xmlGen import XMLGen


class InvenioRecordProcessor(object):

    @classmethod
    def _breakDownCategory(cls, categ, chgSet):

        # categories are never converted to records

        for conf in categ.getAllConferenceList():
            cls._breakDownConference(conf, chgSet)

    @classmethod
    def _breakDownConference(cls, conf, chgSet):

        chgSet.add(conf)

        for contrib in conf.getContributionList():
            cls._breakDownContribution(contrib, chgSet)

    @classmethod
    def _breakDownContribution(cls, contrib, chgSet):

        chgSet.add(contrib)

        for scontrib in contrib.getSubContributionList():
            chgSet.add(scontrib)

    @classmethod
    def _computeProtectionChanges(cls, obj, action, chgSet):
        objType = obj.__class__

        if isinstance(obj, conference.Category):
            cls._breakDownCategory(obj, chgSet)
        elif isinstance(obj, conference.Conference):
            cls._breakDownConference(obj, chgSet)
        elif isinstance(obj, conference.Contribution):
            cls._breakDownContribution(obj, chgSet)
        elif isinstance(obj, conference.SubContribution):
            chgSet.add(obj)

    @classmethod
    def computeRecords(cls, data):
        """
        Receives a sequence of ActionWrappers and returns a sequence
        of records to be updated (created, changed or deleted)
        """

        deleted = set()
        changed = set()
        created = set()
        protectionChanged = set()

        result = []

        print 'Computing records...'

        for ts, aw in data:

            obj = aw.getObject()

            if obj in deleted:
                # previously deleted?
                continue

            for action in aw.getActions():

                if action == 'deleted':
                    # if the record has been deleted, mark it as such
                    # nothing else will matter
                    deleted.add(obj)

                elif action == 'created':
                    # if the record has been created, mark it as such
                    created.add(obj)

                elif action in ['data_changed', 'acl_changed', 'moved']:
                    # categories are ignored
                    if not isinstance(obj, conference.Category):
                        changed.add(obj)

                elif action in ['set_private', 'set_public']:
                    # protection changes have to be handled more carefully
                    cls._computeProtectionChanges(obj, action, protectionChanged)

        print 'Computed records: %s created, %s changed, %s protection' % \
                            (len(created), len(changed), len(protectionChanged))

        for obj in (created | changed | protectionChanged) - deleted:
            yield aw._timestamp, obj, 'create'

        for obj in (deleted):
            yield aw._timestamp, obj, 'delete'

        # TODO: branching to sub objects (i.e. category protection)


class InvenioBatchUploaderAgent(PushSyncAgent):
    """
    Invenio WebUpload-compatible LiveSync agent
    """

    _extraOptions = {'url' : 'Server URL'}

    def __init__(self, aid, name, description, updateTime, url=None):
        super(InvenioBatchUploaderAgent, self).__init__(aid, name, description, updateTime)
        self._url = url

    def _getMetadata(self, operation, record):
        """
        Retrieves the metadata for the record
        """
        xg = XMLGen()
        di = DataInt(xg)

        xg.initXml()

        xg.openTag("collection",[["xmlns","http://www.loc.gov/MARC21/slim"]])

        di.toMarc(record, overrideCache=True, deleted = (operation == 'delete'))

        xg.closeTag("collection")

        return xg.getXml()

    def _upload(self, record, server, data):
        result = server.upload_marcxml(data, "-ir").read()

        self._v_logger.debug('rec %s result: %s' % (record, result))

        if result.startswith('[INFO]'):
            fpath = result.strip().split(' ')[-1]
            self._v_logger.info('rec %s stored in server (%s)' % (record, fpath))
        else:
            self._v_logger.error('rec %s output: %s' % (record, result))
            raise Exception('upload failed')

    def _run(self, manager, data, lastTS):

        uploadedRecords = False
        server = InvenioConnector(self._url)

        # take operations and choose which records to send

        crecords = InvenioRecordProcessor.computeRecords(data)

        self._v_logger.info('Starting metadata/upload cycle')
        for ts, record, operation in crecords:
            # TODO: check operation
            rdata = self._getMetadata(operation, record)
            try:
                self._upload(record, server, rdata)
                uploadedRecords = True
            except:
                self._v_logger.exception('Error uploading data')
                raise AgentExecutionException("Error uploading data")
                # bla bla

        return lastTS if uploadedRecords else None


# Attention: if this class is not declared, the LiveSync management interface
# will never know this plugin exists!

class InvenioAgentProviderComponent(AgentProviderComponent):
    _agentType = InvenioBatchUploaderAgent

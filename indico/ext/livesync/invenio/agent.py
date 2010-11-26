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


from indico.ext.livesync.agent import PushSyncAgent, AgentExecutionException
from indico.ext.livesync.invenio.invenio_connector import InvenioConnector

# legacy OAI/XML libs - this should be replaced soon
from MaKaC.export.oai2 import DataInt
from MaKaC.common.xmlGen import XMLGen

class InvenioRecordProcessor(object):

    @classmethod
    def _computeProtectionChanges(cls, obj, action):
        objType = obj.__class__


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

        for aw in data:

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
                    # if data changed, and there's no other change
                    if obj not in changed:
                        changed.add(obj)

                elif action in ['set_private', 'set_public']:
                    # protection changes have to be handled more carefully
                    cls._computeProtectionChanges(obj, action)

        # TODO - deleted

        for obj in (created | changed):
            yield obj, 'create'

        # TODO: branching to sub objects (i.e. category protection)


class InvenioBatchUploaderAgent(PushSyncAgent):
    """
    Invenio WebUpload-compatible LiveSync agent
    """

    def __init__(self, aid, name, description, updateTime, url):
        super(InvenioBatchUploaderAgent, self).__init__(aid, name, description, updateTime)
        self._url = url

    def _getMetadata(self, record):
        """
        Retrieves the metadata for the record
        """
        di = DataInt(XMLGen())
        return di.toMarc(record)

    def _upload(self, record, server, data):
        result = server.upload_marcxml(data, "-ir")

        self.logger.debug('rec %s result: %s' % (record, result))

        if result.startswith('[INFO]'):
            fpath = result.strip().split(' ')[-1]
            self.logger.info('rec %s stored in server (%s)' % (record, fpath))
        else:
            self.logger.error('rec %s output: %s' % (record, result))

    def _run(self, manager, data):

        server = InvenioConnector(self._url)

        # take operations and choose which records to send
        for record, operation in InvenioRecordProcessor.computeRecords(data):
            # TODO: check operation
            data = self._getMetadata(record)
            try:
                self._upload(record, server, data)
            except:
                self.logger.exception('Error uploading data')
                raise AgentExecutionException("Error uploading data")
                # bla bla

        self.acknowledge()


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

# plugin imports
from indico.ext.livesync.agent import PushSyncAgent
from indico.ext.livesync.metadata import MARCXMLGenerator

# legacy indico
from MaKaC import conference
from MaKaC.accessControl import AccessWrapper
from MaKaC.common.xmlGen import XMLGen

# some useful constants
STATUS_DELETED, STATUS_CREATED, STATUS_CHANGED = 1, 2, 4


# clear the ZEO local cache each new N records
CACHE_SWEEP_LIMIT = 10000


class BistateRecordProcessor(object):

    _lastCacheSweep = 0

    @classmethod
    def _cacheControl(cls, dbi, chgSet):
        if dbi and len(chgSet) > (cls._lastCacheSweep + CACHE_SWEEP_LIMIT):
            # cache sweep
            dbi.sync()
            cls._lastCacheSweep = len(chgSet)

    @classmethod
    def _setStatus(cls, chgSet, obj, state):
        if obj not in chgSet:
            chgSet[obj] = 0
        chgSet[obj] |= state

    @classmethod
    def _breakDownCategory(cls, categ, chgSet, state, dbi=None):

        # categories are never converted to records

        for conf in categ.iterAllConferences():
            cls._breakDownConference(conf, chgSet, state)
            cls._cacheControl(dbi, chgSet)

    @classmethod
    def _breakDownConference(cls, conf, chgSet, state):

        cls._setStatus(chgSet, conf, state)

        for contrib in conf.iterContributions():
            cls._breakDownContribution(contrib, chgSet, state)

    @classmethod
    def _breakDownContribution(cls, contrib, chgSet, state):

        cls._setStatus(chgSet, contrib, state)

        for scontrib in contrib.iterSubContributions():
            cls._setStatus(chgSet, scontrib, state)

    @classmethod
    def _computeProtectionChanges(cls, obj, action, chgSet, dbi=None):
        if isinstance(obj, conference.Category):
            cls._breakDownCategory(obj, chgSet, STATUS_CHANGED, dbi=dbi)
        elif isinstance(obj, conference.Conference):
            cls._breakDownConference(obj, chgSet, STATUS_CHANGED)
        elif isinstance(obj, conference.Contribution):
            cls._breakDownContribution(obj, chgSet, STATUS_CHANGED)
        elif isinstance(obj, conference.SubContribution):
            cls._setStatus(chgSet, obj, STATUS_CHANGED)
        cls._cacheControl(dbi, chgSet)

    @classmethod
    def computeRecords(cls, data, access, dbi=None):
        """
        Receives a sequence of ActionWrappers and returns a sequence
        of records to be updated (created, changed or deleted)
        """

        records = dict()
        deletedIds = dict()

        for __, aw in data:
            obj = aw.getObject()

            ## TODO: enable this, when config is possible from interface
            ## if not obj.canAccess(AccessWrapper(access)):
            ##     # no access? jump over this one
            ##     continue
            for action in aw.getActions():
                if action == 'deleted' and not isinstance(obj, conference.Category):
                    # if the record has been deleted, mark it as such
                    # nothing else will matter
                    deletedIds[obj] = aw.getObjectId()
                    cls._setStatus(records, obj, STATUS_DELETED)

                elif action == 'created' and not isinstance(obj, conference.Category):
                    # if the record has been created, mark it as such
                    cls._setStatus(records, obj, STATUS_CREATED)

                elif action in ['set_private', 'set_public','acl_changed', 'moved']:
                    # protection changes have to be handled more carefully
                    cls._computeProtectionChanges(obj, action, records, dbi=dbi)

                elif action == 'data_changed':
                    if not isinstance(obj, conference.Category):
                        cls._setStatus(records, obj, STATUS_CHANGED)

        for robj, state in records.iteritems():
            if state & STATUS_DELETED:
                yield robj, deletedIds[robj], state
            else:
                yield robj, None, state


class BistateBatchUploaderAgent(PushSyncAgent):
    """
    Invenio WebUpload-compatible LiveSync agent
    """

    _creationState = STATUS_CREATED
    _extraOptions = {'url': 'Server URL'}

    def __init__(self, aid, name, description, updateTime,
                 access=None, url=None):
        super(BistateBatchUploaderAgent, self).__init__(
            aid, name, description, updateTime, access)
        self._url = url

    def record_str(self, (obj, objId, status)):
        """
        Translates the objects/states to an easy to read textual representation
        """

        states = {1: 'DEL', 2: 'CRT', 4: 'MOD'}

        # unfold status
        parts = []
        k = 4
        while (k > 0):
            if status & k:
                parts.append(states[k])
            k /= 2
        return "{0:<40} {1:<20} {2}".format(obj, objId, ' '.join(parts))

    def _getMetadata(self, records, logger=None):
        """
        Retrieves the MARCXML metadata for the record
        """
        xg = XMLGen()
        mg = MARCXMLGenerator(xg)
        # set the permissions
        mg.setPermissionsOf(self._access)

        xg.initXml()
        xg.openTag("collection", [["xmlns", "http://www.loc.gov/MARC21/slim"]])

        for record, recId, operation in records:
            deleted = operation & STATUS_DELETED
            try:
                if deleted:
                    mg.generate(recId, overrideCache=True, deleted=True)
                else:
                    if record.getOwner():
                        # caching is disabled because ACL changes do not trigger
                        # notifyModification, and consequently can be classified as a hit
                        # even if they were changed
                        # TODO: change overrideCache to False when this problem is solved
                        mg.generate(record, overrideCache=True, deleted=False)
                    else:
                        logger.warning('%s (%s) is marked as non-deleted and has no owner' % \
                                       (record, recId))
            except:
                if logger:
                    logger.exception("Something went wrong while processing '%s' (recId=%s) (owner=%s)! Possible metadata errors." %
                                     (record, recId, record.getOwner()))
                    # avoid duplicate record
                self._removeUnfinishedRecord(mg._XMLGen)

        xg.closeTag("collection")

        return xg.getXml()

    def _removeUnfinishedRecord(self, xg):
        """
        gets rid of a remaining '<record>' tag
        """
        # remove any line breaks, etc...
        while not xg.xml[-1].strip():
            xg.xml.pop()
        # remove '<record>'
        xg.xml.pop()

    def _generateRecords(self, data, lastTS, dbi=None):
        return BistateRecordProcessor.computeRecords(data, self._access, dbi=dbi)

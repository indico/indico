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
Module containing the persistent classes that will be stored in the DB
"""
# standard lib imports
import datetime

# dependency libs
import zope.interface
from persistent import Persistent, mapping

# indico extpoint imports
from indico.core.extpoint import Component
from indico.util.fossilize import IFossil, fossilizes, Fossilizable, conversion

# plugin imports
from indico.ext.livesync.struct import SetMultiPointerTrack
from indico.ext.livesync.util import getPluginType
from indico.ext.livesync.struct import EmptyTrackException
from indico.ext.livesync.base import ILiveSyncAgentProvider, MPT_GRANULARITY
from indico.ext.livesync.db import updateDBStructures

# legacy indico imports
from MaKaC import conference
from indico.core.db import DBMgr

class QueryException(Exception):
    """
    Raised by problems in AgentManager queries
    """


class AgentExecutionException(Exception):
    """
    Raised by problems in Agent execution
    """


class IAgentFossil(IFossil):

    def getId(self):
        pass

    def getName(self):
        pass

    def isActive(self):
        pass

    def getDescription(self):
        pass

    def getLastTS(self):
        pass

    def getLastDT(self):
        pass
    getLastDT.convert = conversion.Conversion.datetime

    def getExtraOptions(self):
        pass
    getExtraOptions.name = 'specific'


class SyncAgent(Fossilizable, Persistent):
    """
    Represents an "agent" (service)
    """

    fossilizes(IAgentFossil)

    _extraOptions = {}

    # TODO: Subclass into PushSyncAgent(task)/PullSyncAgent?

    def __init__(self, aid, name, description, updateTime, access=None):
        self._id = aid
        self._name = name
        self._description = description
        self._updateTime = updateTime
        self._manager = None
        self._active = False
        self._recording = False
        self._access = access

    def record_str(self, (obj, objId, status)):
        """
        Translates the objects/states to an easy to read textual representation
        """

    def setManager(self, manager):
        self._manager = manager

    def isActive(self):
        return self._active

    def isRecording(self):
        return self._recording

    def setActive(self, value):
        self._active = value

    def preActivate(self, ts):
        track = self._manager.getTrack()

        try:
            track.movePointer(self._id, ts)
        except EmptyTrackException:
            # if the track is empty, don't bother doing this
            pass

        # this means everything from the pointer to present will be considered
        # when the next update is done
        self._recording = True

    def getId(self):
        return self._id

    def getLastTS(self):
        return self._manager.getTrack().getPointerTimestamp(self._id)

    def getLastDT(self):
        ts = self.getLastTS()
        return datetime.datetime.utcfromtimestamp(ts * self._manager.getGranularity()) if ts else None

    def getName(self):
        return self._name

    def getDescription(self):
        return self._description

    def getExtraOptions(self):
        return dict((option, self.getExtraOption(option))
                    for option in self._extraOptions)

    def getExtraOption(self, optionName):
        if optionName in self._extraOptions:
            return getattr(self, "_%s" % optionName)
        else:
            raise Exception('unknown option!')

    def setExtraOption(self, optionName, value):
        if optionName in self._extraOptions:
            setattr(self, "_%s" % optionName, value)
        else:
            raise Exception('unknown option!')

    def setParameters(self, description=None,
                      name=None):
        if description:
            self._description = description
        if name:
            self._name = name


class AgentProviderComponent(Component):
    """
    This class only serves the purpose of letting LiveSync know that an
    agent type exists
    """

    zope.interface.implements(ILiveSyncAgentProvider)

    # ILiveSyncAgentProvider
    def providesLiveSyncAgentType(self, obj, types):
        if hasattr(self, '_agentType'):
            types[self._agentType.__name__] = self._agentType


class PushSyncAgent(SyncAgent):
    """
    PushSyncAgents are agents that actively send data to remote services,
    instead of waiting to be queried.
    """

    # Should specify which worker will be used
    _workerClass = None

    def __init__(self, aid, name, description, updateTime, access=None):
        """
        :param aid: agent ID
        :param name: agent name
        :param description: a description of the agent
        :param access: an Indico user/group that has equivalent access
        """
        super(PushSyncAgent, self).__init__(aid, name, description, updateTime)
        self._lastTry = None
        self._access = access

    def _run(self, data, logger=None, monitor=None, dbi=None, task=None):
        """
        Overloaded - will contain the specific agent code
        """
        raise Exception("Undefined method")

    def _generateRecords(self, data, lastTS, dbi=None):
        """
        :param data: iterable containing data to be converted
        :param lastTS:

        Takes the raw data (i.e. "event created", etc) and transforms
        it into a sequence of 'record/action' pairs.

        Basically, this function reduces actions to remove server "commands"

        i.e. ``modified 1234, deleted 1234`` becomes just ``delete 1234``

        Overloaded by agents
        """

    def run(self, currentTS, logger=None, monitor=None, dbi=None, task=None):
        """
        Main method, called when agent needs to be run
        """

        if currentTS == None:
            till = None
        else:
            till = currentTS / self._manager.getGranularity() - 1

        if not self._manager:
            raise AgentExecutionException("SyncAgent '%s' has no manager!" % \
                                          self._id)

        if logger:
            logger.info("Querying agent %s for events till %s" % \
                        (self.getId(), till))

        # query till currentTS - 1, for integrity reasons
        data = self._manager.query(agentId=self.getId(),
                                   till=till)

        try:
            records = self._generateRecords(data, till, dbi=dbi)
            # run agent-specific cycle
            result = self._run(records, logger=logger, monitor=monitor, dbi=dbi, task=task)
        except:
            if logger:
                logger.exception("Problem running agent %s" % self.getId())
            return None

        if result != None:
            self._lastTry = till
            return self._lastTry
        else:
            return None

    def acknowledge(self):
        """
        Called to signal that the information has been correctly processed
        (usually called by periodic task)
        """
        self._manager.advance(self.getId(), self._lastTry)


class SyncManager(Persistent):
    """
    Stores live sync configuration parameters and "agents". It is  basically an
    "Agent Manager"
    """

    def __init__(self, granularity=MPT_GRANULARITY):
        """
        :param granularity: integer, number of seconds per MPT entry
        """
        self._granularity = granularity
        self.reset()

    def getGranularity(self):
        """
        Returns the granularity that is set for the MPT
        """
        return self._granularity

    @classmethod
    def getDBInstance(cls):
        """
        Returns the instance of SyncManager currently in the DB
        """
        storage = getPluginType().getStorage()
        if 'agent_manager' in storage:
            return storage['agent_manager']
        else:
            root = DBMgr.getInstance().getDBConnection()
            updateDBStructures(root)

    def reset(self, agentsOnly=False, trackOnly=False):
        """
        Resets database structures

        .. WARNING::
           This erases any agents and contents in the MPT
        """
        if not trackOnly:
            self._agents = mapping.PersistentMapping()
        if not agentsOnly:
            self._track = SetMultiPointerTrack()

    def registerNewAgent(self, agent):
        """
        Registers the agent, placing it in a mapping structure
        """
        self._agents[agent.getId()] = agent

        # create a new pointer in the track
        self._track.addPointer(agent.getId())

        # impose myself as its manager
        agent.setManager(self)

    def removeAgent(self, agent):
        """
        Removes an agent
        """
        self._track.removePointer(agent.getId())
        del self._agents[agent.getId()]

    def query(self, agentId=None, till=None):
        """
        Queries the agent for a given timespan
        """

        # TODO: Add more criteria! (for now this will do)

        if agentId == None:
            raise QueryException("No criteria specified!")

        return self._track.pointerIterItems(agentId, till=till)

    def advance(self, agentId, newLastTS):
        """
        Advances the agent "pointer" to the specified timestamp
        """
        self._track.movePointer(agentId,
                                newLastTS)

    def add(self, timestamp, action):
        """
        Adds a specific action to the specified timestamp
        """
        self._track.add(timestamp / self._granularity, action)

    def getTrack(self):
        """
        Rerturns the MPT
        """
        return self._track

    def getAllAgents(self):
        """
        Returns the agent dictionary
        """
        return self._agents

    def objectExcluded(self, obj):
        """
        Decides whether a particular object should be ignored or not
        """
        excluded = getPluginType().getOption('excludedCategories').getValue()

        if isinstance(obj, conference.SessionSlot):
            return True
        elif isinstance(obj, conference.Category):
            return obj.getId() in excluded
        elif isinstance(obj, conference.Conference):
            owner = obj.getOwner()
            if owner:
                return owner.getId() in excluded
        elif obj.getParent():
            conf = obj.getConference()
            if conf:
                owner = conf.getOwner()
                if owner:
                    return owner.getId() in excluded

        return False


class RecordUploader(object):
    """
    Encapsulates record uploading behavior.
    """

    DEFAULT_BATCH_SIZE, DEFAULT_NUM_SLAVES = 1000, 2

    def __init__(self, logger, agent, batchSize=DEFAULT_BATCH_SIZE):
        self._logger = logger
        self._agent = agent
        self._batchSize = batchSize

    def _uploadBatch(self, batch):
        """
        :param batch: list of records

        To be overloaded by uploaders. Does the actual upload.
        """
        raise Exception("Unimplemented method!")

    def iterateOver(self, iterator, dbi=None):
        """
        Consumes an iterator, uploading the records that are returned
        `dbi` can be passed, so that the cache is cleared once in a while
        """

        currentBatch = []

        # take operations and choose which records to send
        for record in iterator:
            if len(currentBatch) > (self._batchSize - 1):
                self._uploadBatch(currentBatch)
                currentBatch = []

            currentBatch.append(record)

            if dbi:
                dbi.abort()

        if currentBatch:
            self._uploadBatch(currentBatch)

        return True

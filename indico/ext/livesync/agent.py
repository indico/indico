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
Module containing the persistent classes that will be stored in the DB
"""
# standard lib imports
import datetime, time
from threading import Thread
from Queue import Queue, Empty

# dependency libs
import zope.interface
from persistent import Persistent, mapping

# indico api imports
from indico.core.api import Component
from indico.util.fossilize import IFossil, fossilizes, Fossilizable, conversion

# plugin imports
from indico.ext.livesync.struct import SetMultiPointerTrack
from indico.ext.livesync.util import getPluginType
from indico.ext.livesync.struct import EmptyTrackException
from indico.ext.livesync.base import ILiveSyncAgentProvider

# legacy indico
from MaKaC.common import DBMgr


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

    def __init__(self, aid, name, description, updateTime):
        self._id = aid
        self._name = name
        self._description = description
        self._updateTime = updateTime
        self._manager = None
        self._active = False
        self._recording = True

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
            track.movePointer(self._id, track.mostRecentTS(ts))
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
        return datetime.datetime.utcfromtimestamp(ts) if ts else None

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
    Base class for PushSyncAgents
    """

    # Should specify which worker will be used
    _workerClass = None

    def __init__(self, aid, name, description, updateTime):
        super(PushSyncAgent, self).__init__(aid, name, description, updateTime)
        self._lastTry = None

    def _run(self, data, logger=None, monitor=None):
        """
        Overloaded - will contain the specific agent code
        """
        raise Exception("Undefined method")

    def _generateRecords(self, data, lastTS):
        """
        Takes the raw data (i.e. "event created", etc) and transforms
        it into a sequence of 'record/action' pairs.

        Basically ,this function reduces actions to remove server "commands"

        i.e. "modified 1234, deleted 1234" becomes just "delete 1234"

        Overloaded by agents
        """

    def run(self, currentTS, logger=None, monitor=None):
        """
        Main method, called when agent needs to be run
        """

        if currentTS == None:
            till = None
        else:
            till = currentTS - 1

        if not self._manager:
            raise AgentExecutionException("SyncAgent '%s' has no manager!" % \
                                          self._id)

        # query till currentTS - 1, for integrity reasons
        data = self._manager.query(agentId=self.getId(),
                                   till=till)

        if logger:
            logger.info("Querying agent %s for events till %s" % \
                        (self.getId(), till))

        try:
            records = self._generateRecords(data, till)
            # run agent-specific cycle
            result = self._run(records, logger=logger, monitor=monitor)
        except:
            if logger:
                logger.exception("Problem running agent %s" % self.getId())
            return None

        if result:
            self._lastTry = till
            return self._lastTry
        else:
            return None

    def acknowledge(self):
        """
        Called to signal that the information has been correctly processed
        """
        self._manager.advance(self.getId(), self._lastTry)


class SyncManager(Persistent):
    """
    Stores live sync configuration parameters and "agents". It is  basically an
    "Agent Manager"
    """

    @classmethod
    def getDBInstance(cls):
        storage = getPluginType().getStorage()
        return storage['agent_manager']

    def __init__(self):
        self.reset()

    def reset(self, agentsOnly=False, trackOnly=False):
        """
        Resets database structures
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
                                self._track.mostRecentTS(newLastTS))

    def add(self, timestamp, action):
        """
        Adds a specific action to the specified timestamp
        """
        if type(action) == list:
            for a in action:
                # TODO: bulk add at low level?
                self._track.add(timestamp, a)
        else:
            # TODO: timestamp conversion (granularity)!
            self._track.add(timestamp, action)

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


class RecordUploader(object):

    DEFAULT_BATCH_SIZE, DEFAULT_NUM_SLAVES = 1000, 2

    def __init__(self, logger, agent, batchSize=DEFAULT_BATCH_SIZE):
        self._logger = logger
        self._agent = agent
        self._batchSize = batchSize

    def _uploadBatch(self, batch):
        """
        To be overloaded by uploaders
        """
        raise Exception("Unimplemented method!")

    def iterateOver(self, iterator):
        """
        Consumes an iterator
        """

        currentBatch = []

        # take operations and choose which records to send
        for record in iterator:

            if len(currentBatch) > (self._batchSize - 1):
                self._uploadBatch(currentBatch)
                currentBatch = []

            currentBatch.append(record)

        if currentBatch:
            self._uploadBatch(currentBatch)

        return True

###################
# This code is now unused.
#
#

class ThreadedRecordUploader(object):
    """
    A record uploading mechanism, based on worker threads
    """

    DEFAULT_BATCH_SIZE, DEFAULT_NUM_SLAVES = 1000, 2
    MAX_DELAYED_BATCHES = 5

    def __init__(self, slaveClass, logger,
                 extraSlaveArgs=(),
                 batchSize=DEFAULT_BATCH_SIZE,
                 numSlaves=DEFAULT_NUM_SLAVES,
                 maxDelayed=MAX_DELAYED_BATCHES,
                 monitor=None):
        self._logger = logger
        self._slaveClass = slaveClass
        self._batchSize = batchSize
        self._numSlaves = numSlaves
        self._queue = Queue()
        self._slaves = {}
        self._currentBatch = []
        self._extraSlaveArgs = extraSlaveArgs
        self._enqueued = 0
        self._monitor = monitor
        self._maxDelayed = maxDelayed

    def spawn(self):
        """
        Starts the uploader (spawns slave threads)
        """
        for i in range(0, self._numSlaves):
            self._slaves[i] = self._slaveClass("Uploader%s" % i,
                                               self._queue,
                                               self._logger,
                                               *self._extraSlaveArgs)
            self._slaves[i].start()

    def enqueue(self, record):
        """
        Adds a record to the queue.
        We actually accumulate them and queue them in batches.
        """

        # when BATCH_SIZE is passed, enqueue it
        if len(self._currentBatch) > (self._batchSize - 1):
            self._queue.put(self._currentBatch)
            self._enqueued += len(self._currentBatch)
            self._currentBatch = []

            if self._monitor:
                self.reportStatus(self._monitor)

        self._currentBatch.append(record)

    def join(self):
        """
        Waits for the slave threads to finish working
        """

        result = True

        # first, if there is an incomplete batch remaining, enqueue it first
        if self._currentBatch:
            self._queue.put(self._currentBatch)

        # now, join the queue (wait for them to be uploaded)
        self._logger.debug('joining queue')
        self._queue.join()
        self._logger.debug('joining slaves')

        for slave in self._slaves.values():
            slave.terminate()
            slave.join()
            result &= (not slave.is_alive() and slave.result)

        return result

    def _checkThreadHealth(self):
        for i in range(0, self._numSlaves):
            slave = self._slaves[i]
            if time.time() > (slave._startTime + \
                              ThreadedRecordUploader.MAX_THREAD_REQUEST_TIME) \
               and slave._dead == False:
                self._logger.warning("Slave '%s' seems to be dead. "
                                     "Adding another one and recovering batch." % \
                                     slave.getName())

                if slave._currentBatch:
                    self._queue.put(slave._currentBatch)

                newSlave = self._slaveClass("Uploader%s" % self._numSlaves,
                                            self._queue,
                                            self._logger,
                                            self._agent,
                                            *self._extraSlaveArgs)
                self._slaves[self._numSlaves] = newSlave
                slave._dead = True
                self._numSlaves += 1

                newSlave.start()

    def iterateOver(self, iterator):
        """
        Consumes an iterator
        """
        # take operations and choose which records to send
        for entry in iterator:
            self.enqueue(entry)

            while (self._queue.qsize() > self._maxDelayed):
                self._logger.info('Too many delayed batches, sleeping')
                time.sleep(10)

    def reportStatus(self, stream):
        totalUp = 0
        stream.write("%d enqueued\n" % self._enqueued)
        for i in range(0, self._numSlaves):
            slave = self._slaves[i]
            stream.write("\t [wrk %s] %d uploaded\n" % (slave.getName(),
                                                     slave._uploaded))
            totalUp += slave._uploaded
        stream.write("%d uploaded (total)\n\n" % totalUp)
        stream.flush()


class UploaderSlave(Thread):
    """
    A generic threaded "work slave" for agents
    """

    def __init__(self, name, queue, logger, agent):
        self._keepRunning = True
        self._logger = logger
        self._terminate = False
        self.result = True
        self._queue = queue
        self._name = name
        self._uploaded = 0
        self._agent = agent
        self._startTime = time.time()
        self._currentBatch = []
        self._dead = False

        super(UploaderSlave, self).__init__(name=name)

    def run(self):

        DBMgr.getInstance().startRequest()

        self._logger.debug('Worker [%s] started' % self._name)
        try:
            while True:
                taskFetched = False
                try:
                    self._currentBatch = self._queue.get(True, 2)
                    taskFetched = True
                    self._startTime = time.time()
                    self.result &= self._uploadBatch(self._currentBatch)
                    self._uploaded += len(self._currentBatch)
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
        self._terminate = True

    def _uploadBatch(self, batch):
        """
        Sends a batch of records
        Overloaded by agent.
        """
        raise Exception("Unimplemented method")

    def _getMetadata(self, records):
        """
        Generates the metadata for a batch of records.
        Should be overloaded.
        """
        raise Exception("Unimplemented method")


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

from dateutil import rrule
from datetime import timedelta

from BTrees.IOBTree import IOBTree

from indico.util.fossilize import fossilizes
from indico.modules.scheduler import base
from indico.modules.scheduler.tasks import BaseTask, TimedEvent
from indico.modules.scheduler.fossils import ITaskOccurrenceFossil


class PeriodicTask(BaseTask):
    """
    Tasks that should be executed at regular intervals
    """

    def __init__(self, frequency, **kwargs):
        """
        :param frequency: a valid dateutil frequency specifier (DAILY, HOURLY, etc...)
        """
        super(PeriodicTask, self).__init__()

        self._nextOccurrence = None
        self._lastFinishedOn = None
        self._occurrences = IOBTree()
        self._occurrenceCount = 0
        self._repeat = True

        if 'dtstart' not in kwargs:
            kwargs['dtstart'] = self._getCurrentDateTime()

        self._rule = rrule.rrule(
            frequency,
            **kwargs
            )

        self._nextOccurrence = self._rule.after(
            kwargs['dtstart'] - timedelta(seconds=1),
            inc=True)

    def start(self, delay):
        super(PeriodicTask, self).start(delay)

    def tearDown(self):
        super(PeriodicTask, self).tearDown()

    def setNextOccurrence(self, dateAfter=None):

        if not self._nextOccurrence:
            # if it's None already, it means there's no "future"
            return

        if not dateAfter:
            dateAfter = self._getCurrentDateTime()

        # find next date after
        nextOcc = self._rule.after(max(self._nextOccurrence, dateAfter),
                                   inc=False)

        # repeat process till a satisfactory date is found
        # or there is nothing left to check
        #while nextOcc and nextOcc < dateAfter:
        #    nextOcc = self._rule.after(nextOcc,
        #                               inc = False)

        self._nextOccurrence = nextOcc
        return nextOcc

    def getStartOn(self):
        return self._nextOccurrence

    def getLastFinishedOn(self):
        return self._lastFinishedOn

    def addOccurrence(self, occurrence):
        occurrence.setId(self._occurrenceCount)
        self._occurrences[self._occurrenceCount] = occurrence
        self._occurrenceCount += 1

    def dontComeBack(self):
        self._repeat = False

    def shouldComeBack(self):
        return self._repeat


class PeriodicUniqueTask(PeriodicTask):
    """
    Singleton periodic tasks: no two or more PeriodicUniqueTask of this
    class will be queued or running at the same time (TODO)
    """
    # TODO: implement this


class TaskOccurrence(TimedEvent):
    """
    Wraps around a PeriodicTask object, and represents an occurrence of this task
    """

    fossilizes(ITaskOccurrenceFossil)

    def __init__(self, task):
        self._task = task
        self._startedOn = task.getStartedOn()
        self._endedOn = task.getEndedOn()
        self._id = None

    def __cmp__(self, obj):
        if obj is None:
            return 1
        elif isinstance(obj, BaseTask):
            task_cmp = cmp(self.getTask(), obj)
            if task_cmp == 0:
                return 1
            else:
                return task_cmp
        elif not isinstance(obj, TaskOccurrence) or (self._id == obj._id and self._id is None):
            return cmp(hash(self), hash(obj))

        occ_task_cmp = cmp(self.getTask(), obj.getTask())
        if occ_task_cmp == 0:
            return cmp(self.getId(), obj.getId())
        else:
            return occ_task_cmp

    def getId(self):
        return self._id

    def getUniqueId(self):
        return "%s:%s" % (self._task.getUniqueId(), self._id)

    def setId(self, occId):
        self._id = occId

    def getStartedOn(self):
        return self._startedOn

    def getEndedOn(self):
        return self._endedOn

    def getTask(self):
        return self._task


class CategoryStatisticsUpdaterTask(PeriodicUniqueTask):
    '''Updates statistics associated with categories
    '''

    # seconds to consider a task AWOL
    _AWOLThresold = 15000

    def __init__(self, cat, frequency, **kwargs):
        super(CategoryStatisticsUpdaterTask, self).__init__(frequency,
                                                            **kwargs)
        self._cat = cat

    def run(self):
        from MaKaC.statistics import CategoryStatistics
        CategoryStatistics.updateStatistics(self._cat,
                                            self.getLogger())


# TODO: Isolate CERN Specific
class FoundationSyncTask(PeriodicUniqueTask):
    """
    Synchronizes room data (along with associated room managers
    and equipment) with Foundation database.

    Also, updates list of CERN Official Holidays

    (This is object for a task class)
    """
    def __init__(self, frequency, **kwargs):
        super(FoundationSyncTask, self).__init__(frequency, **kwargs)

    def run(self):
        from MaKaC.common.FoundationSync.foundationSync import FoundationSync
        FoundationSync(self.getLogger()).doAll(None)


class SamplePeriodicTask(PeriodicTask):
    def run(self):
        base.TimeSource.get().sleep(1)
        self.getLogger().debug('%s executed' % self.__class__.__name__)

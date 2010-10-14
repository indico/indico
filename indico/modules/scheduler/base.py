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

import time
from contextlib import contextmanager
from ZODB.POSException import ConflictError

from indico.util.date_time import nowutc

TASK_STATUS_NONE, TASK_STATUS_SPOOLED, TASK_STATUS_QUEUED, TASK_STATUS_RUNNING, \
TASK_STATUS_FAILED, TASK_STATUS_ABORTED, TASK_STATUS_FINISHED = range(0,7)

# threading vs. multiprocessing

CONFLICTERROR_MAX_RETRIES = 10

class OperationManager(object):
    """
    Takes care of synchronizing resources
    """

    def __init__(self, dbi, logger = None):
        self._dbi = dbi
        self._logger = logger

    @contextmanager
    def commit(self, sync = False):

        for i in range(CONFLICTERROR_MAX_RETRIES):
            if sync:
                self._dbi.sync()
            yield
            try:
                self._dbi.commit()
            except ConflictError:
                sync = True
                self._logger.debug("Commit failed (%d)" % i)
            else:
                break
        else:
            if self._logger:
                self._logger.error("Commit failed %d consecutive times. "
                                   "Something bad must be going on..." %
                                   CONFLICTERROR_MAX_RETRIES)


## Time Sources

class TimeSource(object):
    """
    A class that represents a time source (a reference clock)
    This abstraction may look a bit of an overkill, but it is very
    useful for testing purposes
    """

    @classmethod
    def get(cls):
        return cls._source

    @classmethod
    def set(cls, source):
        cls._source = source

    def __init__(self):
        super(TimeSource, self).__init__()

    def sleep(self, amount):
        time.sleep(amount)

    def getCurrentTime():
        """
        Returns the current datetime
        """
        raise Exception('Undefined method! Should be overloaded.')


class UTCTimeSource(TimeSource):

    def getCurrentTime(self):
        return nowutc()

TimeSource._source = UTCTimeSource()

## Exceptions

class SchedulerException(Exception):
    pass


class TaskStillRunningException(SchedulerException):
    def __init__(self, task):
        SchedulerException.__init__(self, 'Task %s (%s) is currently running' %
                                    (task.id, task.typeId))

class TaskNotFoundException(SchedulerException):
    pass


class TaskInconsistentStatusException(SchedulerException):
    pass

class SchedulerQuitException(SchedulerException):
    pass

class SchedulerUnknownOperationException(SchedulerException):
    pass

class SchedulerConfigurationException(SchedulerException):
    pass


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

import time
import types
from ZODB.POSException import ConflictError

from indico.util.date_time import nowutc

TASK_STATUS_NONE, TASK_STATUS_SPOOLED, TASK_STATUS_QUEUED, \
TASK_STATUS_RUNNING, TASK_STATUS_FAILED, TASK_STATUS_ABORTED, \
TASK_STATUS_FINISHED, TASK_STATUS_TERMINATED = range(0,8)


def status(num):
    return ['NN', 'SP', 'QD', 'RN', 'FA', 'AB',
            'FI', 'TD'][num]


CONFLICTERROR_MAX_RETRIES = 10


class OperationManager(object):
    """
    Takes care of synchronizing resources
    """

    def __init__(self, f):
        self._f = f

    def __get__(self, obj, ownerClass=None):
        return types.MethodType(self, obj)

    def __call__(self, zelf, *args, **kwargs):
        # some magic introspection
        logger = zelf._logger
        dbi = zelf._dbi
        sync = False

        logger.debug("START Critical section around  %s" % self._f.__name__)

        for i in range(CONFLICTERROR_MAX_RETRIES):
            if sync:
                dbi.sync()
            retValue = self._f(zelf, *args, **kwargs)
            try:
                dbi.commit()
            except Exception, e:
                logger.exception("Commit failed (%d)" % i)
                if isinstance(e, ConflictError):
                    sync = True
                else:
                    raise
            else:
                break
        else:
            logger.error("Commit failed %d consecutive times. "
                         "Something bad must be going on..." %
                         CONFLICTERROR_MAX_RETRIES)

        logger.debug("END Critical section")

        return retValue


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

    def getCurrentTime(self):
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
        SchedulerException.__init__(self, '%s is currently running' % task)


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

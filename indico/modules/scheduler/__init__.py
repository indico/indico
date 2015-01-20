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
The ``scheduler`` module provides Indico with a scheduling API that allows specific jobs
(tasks to be run at given times, with a certain repeatibility, if needed).
"""

class TaskDelayed(Exception):
    def __init__(self, seconds):
        self.delaySeconds = seconds

from indico.modules.scheduler.module import SchedulerModule
from indico.modules.scheduler.server import Scheduler
from indico.modules.scheduler.client import Client
from indico.modules.scheduler.tasks import OneShotTask
from indico.modules.scheduler.tasks.periodic import PeriodicTask

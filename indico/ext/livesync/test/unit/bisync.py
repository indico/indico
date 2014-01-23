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

from indico.ext.livesync.bistate import BistateRecordProcessor, \
     STATUS_DELETED, STATUS_CREATED, STATUS_CHANGED
from indico.ext.livesync import ActionWrapper

from indico.tests.python.unit.util import IndicoTestCase


class DummyWrapper(object):
    def __init__(self, name):
        self._name = name

    def canAccess(self, whatever):
        return True

    def __str__(self):
        return "Dummy %s" % self._name


class TestInvenioRecordProcessor(IndicoTestCase):

    def testEventWorkflow(self):
        evt1 = DummyWrapper('evt1')
        evt2 = DummyWrapper('evt2')

        self.assertEqual(
            set(list(BistateRecordProcessor.computeRecords([
                (1, ActionWrapper(1, evt1,
                                  ['data_changed', 'created'])),
                (2, ActionWrapper(1, evt2,
                                  ['data_changed', 'created'])),
                (3, ActionWrapper(2, evt1,
                                  ['deleted'])),
                (4, ActionWrapper(2, evt2,
                                 ['data_changed']))], None))),
            set([(evt1, STATUS_CREATED | STATUS_CHANGED | STATUS_DELETED),
             (evt2, STATUS_CREATED | STATUS_CHANGED)]))

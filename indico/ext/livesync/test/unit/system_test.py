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
System tests for indico.ext.livesync

Here, the notification parts of the plugin are tested in a global way.
"""

from indico.util.i18n import currentLocale
from indico.tests.python.unit.util import IndicoTestCase

# plugin imports
from indico.ext.livesync.test.unit.base import _TestSynchronization


class TestBasicOperations(_TestSynchronization, IndicoTestCase):

    def testEventCreation(self):
        """
        Create an event
        """

        with self._context('database', 'request'):
            conf1 = self._home.newConference(self._dummy)

        self.checkActions(0, set([(self._home, 'data_changed'),
                                  (conf1, 'created data_changed')]))

        ts = self._nextTS()

        with self._context('database', 'request'):
            conf2 = self._home.newConference(self._dummy)

        self.checkActions(ts, set([(self._home, 'data_changed'),
                                   (conf2, 'created data_changed')]))

    def testEventTitleChange(self):
        """
        Change the title of an event
        """

        with self._context('database', 'request'):
            conf1 = self._home.newConference(self._dummy)

        ts = self._nextTS()

        with self._context('database', 'request'):
            conf1.setTitle('1234 test')

        self.checkActions(ts, set([(conf1, 'data_changed title_changed')]))

    def testEventDelete(self):
        """
        Delete an event
        """

        with self._context('database', 'request'):
            conf1 = self._home.newConference(self._dummy)

        ts = self._nextTS()

        with self._context('database', 'request'):
            conf1.delete()

        self.checkActions(ts, set([(conf1, 'data_changed deleted')]))

    def testCategoryCreateDelete(self):
        """
        Create/delete categories
        """

        with self._context('database', 'request'):
            categ1 = self._home.newSubCategory(1)
            categ2 = categ1.newSubCategory(0)

        self.checkActions(0, set([(self._home, 'data_changed'),
                                  (categ1, 'created data_changed set_private'),
                                  (categ2, 'created')]))

        ts = self._nextTS()

        with self._context('database', 'request'):
            categ1.delete()

        self.checkActions(ts, set([(categ1, 'deleted'),
                                   (categ2, 'deleted')]))

    def testCategoryMove(self):
        """
        Move a category around
        """

        with self._context('database', 'request'):
            categ1 = self._home.newSubCategory(1)
            categ2 = self._home.newSubCategory(0)
            categ3 = categ1.newSubCategory(0)

        self.checkActions(0, set([(self._home, 'data_changed'),
                                  (categ1, 'created data_changed set_private'),
                                   (categ2, 'created'),
                                   (categ3, 'created')]))

        ts = self._nextTS()

        with self._context('database', 'request'):
            categ3.move(categ2)

        self.checkActions(ts, set([(categ3, 'moved set_public')]))

    def testEventCreateDeleteInside(self):
        """
        Create an event (and things inside) and delete it
        """

        with self._context('database', 'request'):
            conf1 = self._home.newConference(self._dummy)
            cont1 = conf1.newContribution()
            cont2 = conf1.newContribution()
            scont1 = cont1.newSubContribution()

        self.checkActions(0, set([(self._home, 'data_changed'),
                                  (conf1, 'created data_changed'),
                                  (cont1, 'created data_changed'),
                                  (cont2, 'created'),
                                  (scont1, 'created')]))
        ts = self._nextTS()

        with self._context('database', 'request'):
            conf1.delete()

        self.checkActions(ts, set([(conf1, 'data_changed deleted'),
                                   (cont1, 'deleted'),
                                   (cont2, 'deleted'),
                                   (scont1, 'deleted')]))


class TestProtectionChanges(_TestSynchronization, IndicoTestCase):

    def testDirectConferenceProtectionChanges(self):
        """
        Change protection of conferences, directly
        """

        # setup
        with self._context('database', 'request'):
            categ1 = self._home.newSubCategory(1)
            categ2 = self._home.newSubCategory(0)
            conf1 = categ1.newConference(self._dummy)
            conf2 = categ2.newConference(self._dummy)

        ts = self._nextTS()

        # move them around
        with self._context('database', 'request'):
            conf1.setProtection(-1)
            conf2.setProtection(1)

        # events should change from public <-> private
        self.checkActions(ts, set([(conf1, 'set_public'),
                                   (conf2, 'set_private')]))

    def testIndirectConferenceProtectionChanges(self):
        """
        Change protection of conferences, through moving them
        """

        # setup
        with self._context('database', 'request'):
            categ1 = self._home.newSubCategory(1)
            categ2 = self._home.newSubCategory(0)
            conf1 = categ1.newConference(self._dummy)
            conf2 = categ2.newConference(self._dummy)

        ts = self._nextTS()

        # move them around
        with self._context('database', 'request'):
            categ1.moveConference(conf1, categ2)
            categ2.moveConference(conf2, categ1)

        # events should change from public <-> private
        self.checkActions(ts, set([(conf1, 'data_changed moved set_public'),
                                   (conf2, 'data_changed moved set_private')]))

        ts = self._nextTS()

        # switch category protection
        with self._context('database', 'request'):
            categ1.setProtection(0)
            categ2.setProtection(1)

        # categories should be the only ones changed
        # (because events will be changed indirectly)
        self.checkActions(ts, set([
            (categ1, 'set_public'),
            (categ2, 'set_private')]))

# TODO
# * Contributions
# * Subcontributions

# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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

from datetime import datetime
from pytz import timezone

from MaKaC.user import Avatar
from MaKaC.conference import AvatarHolder, ConferenceHolder
from MaKaC import conference as conf
from indico.tests.python.unit.util import IndicoTestCase, with_context

from MaKaC.plugins import PluginsHolder
from indico.ext.calendaring.storage import getAvatarConferenceStorage, addAvatarConference
from indico.ext.calendaring.outlook.tasks import OutlookUpdateCalendarNotificationTask
from dateutil.rrule import MINUTELY


class TestTasks(IndicoTestCase):
    """ Tests outlook plugin tasks operations
    """

    _requires = ['db.Database', 'db.DummyUser']

    def setUp(self):
        super(TestTasks, self).setUp()
        self._startDBReq()

        PluginsHolder().updateAllPluginInfo()

        # Create two dummy users
        ah = AvatarHolder()
        self._avatar1 = ah.getById(0)
        self._avatar2 = Avatar()
        self._avatar2.setName("fake-2")
        self._avatar2.setSurName("fake")
        self._avatar2.setOrganisation("fake")
        self._avatar2.setLang("en_GB")
        self._avatar2.setEmail("fake2@fake.fake")
        ah.add(self._avatar2)

        # Create two dummy conferences
        category = conf.CategoryManager().getById('0')
        ch = ConferenceHolder()

        self._conf1 = category.newConference(self._avatar1)
        self._conf1.setTimezone('UTC')
        sd1 = datetime(2012, 12, 1, 10, 0, tzinfo=timezone('UTC'))
        ed1 = datetime(2012, 12, 1, 18, 0, tzinfo=timezone('UTC'))
        self._conf1.setDates(sd1, ed1)
        ch.add(self._conf1)

        self._conf2 = category.newConference(self._avatar2)
        self._conf2.setTimezone('UTC')
        sd2 = datetime(2012, 12, 10, 11, 0, tzinfo=timezone('UTC'))
        ed2 = datetime(2012, 12, 11, 13, 0, tzinfo=timezone('UTC'))
        self._conf2.setDates(sd2, ed2)
        ch.add(self._conf2)

        self._stopDBReq()

    @with_context('database')
    def testOutlookRunTask(self):
        """ Tests outlook notification scheduler task.
            Using mock to avoid running real POST requests.
        """

        mockReturn = []

        def mock_sendEventRequest(self, key, eventType, avatar, conference, plugin):
            if avatar.getName() == 'fake-2' and conference.getId() == '0':
                mockReturn.append(200)
                return 200
            if avatar.getName() == 'fake-2' and conference.getId() == '1' and eventType == "added":
                mockReturn.append(200)
                return 200
            mockReturn.append(None)
            return None

        OutlookUpdateCalendarNotificationTask._sendEventRequest = mock_sendEventRequest
        outlookTask = OutlookUpdateCalendarNotificationTask(MINUTELY)

        storage = getAvatarConferenceStorage()

        addAvatarConference(self._avatar1, self._conf1, "added")
        addAvatarConference(self._avatar1, self._conf1, "removed")
        addAvatarConference(self._avatar2, self._conf2, "added")
        addAvatarConference(self._avatar2, self._conf2, "removed")
        outlookTask.run()
        self.assertEqual(mockReturn, [None, None, 200, None])
        self.assertEqual(len(storage), 2)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf1.getId()]), 2)
        self.assertEqual(len(storage[self._avatar2.getId() + '_' + self._conf2.getId()]), 2)
        mockReturn = []

        addAvatarConference(self._avatar2, self._conf1, "added")
        addAvatarConference(self._avatar2, self._conf1, "removed")
        outlookTask.run()
        self.assertEqual(mockReturn, [None, None, 200, 200, None, None])
        self.assertEqual(len(storage), 2)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf1.getId()]), 2)
        self.assertEqual(len(storage[self._avatar2.getId() + '_' + self._conf2.getId()]), 2)
        mockReturn = []

        addAvatarConference(self._avatar1, self._conf1, "added")
        addAvatarConference(self._avatar1, self._conf2, "removed")
        outlookTask.run()
        self.assertEqual(mockReturn, [None, None, None, None, None, None])
        self.assertEqual(len(storage), 3)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf1.getId()]), 3)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf2.getId()]), 1)
        self.assertEqual(len(storage[self._avatar2.getId() + '_' + self._conf2.getId()]), 2)
        mockReturn = []

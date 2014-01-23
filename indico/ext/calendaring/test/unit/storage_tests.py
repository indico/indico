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

from datetime import datetime
from pytz import timezone

from MaKaC.user import Avatar
from MaKaC.conference import AvatarHolder, ConferenceHolder
from MaKaC import conference as conf
from indico.tests.python.unit.util import IndicoTestCase, with_context

from MaKaC.plugins import PluginsHolder
from indico.ext.calendaring.storage import getAvatarConferenceStorage, addAvatarConference, updateConference

from MaKaC.participant import Participant
from MaKaC.registration import Registrant


class TestStorage(IndicoTestCase):
    """ Tests plugin storage management
    """

    _requires = ['db.Database', 'db.DummyUser']

    def setUp(self):
        super(TestStorage, self).setUp()
        self._startDBReq()

        PluginsHolder().updateAllPluginInfo()
        PluginsHolder().getPluginType('calendaring').setActive(True)
        PluginsHolder().getPluginType('calendaring').getPlugin('outlook').setActive(True)

        # Create two dummy users
        ah = AvatarHolder()
        self._avatar1 = Avatar()
        self._avatar1.setName("fake-3")
        self._avatar1.setSurName("fake3")
        self._avatar1.setOrganisation("fake3")
        self._avatar1.setEmail("fake3@fake3.fake")
        ah.add(self._avatar1)
        self._avatar2 = Avatar()
        self._avatar2.setName("fake-4")
        self._avatar2.setSurName("fake4")
        self._avatar2.setOrganisation("fake4")
        self._avatar2.setEmail("fake4@fake4.fake")
        ah.add(self._avatar2)

        # Create two dummy conferences
        category = conf.CategoryManager().getById('0')
        ch = ConferenceHolder()

        self._conf1 = category.newConference(self._avatar1)
        self._conf1.setTimezone('UTC')
        sd1 = datetime(2020, 12, 1, 10, 0, tzinfo=timezone('UTC'))
        ed1 = datetime(2020, 12, 1, 18, 0, tzinfo=timezone('UTC'))
        self._conf1.setDates(sd1, ed1)
        ch.add(self._conf1)

        self._conf2 = category.newConference(self._avatar2)
        self._conf2.setTimezone('UTC')
        sd2 = datetime(2020, 12, 10, 11, 0, tzinfo=timezone('UTC'))
        ed2 = datetime(2020, 12, 11, 13, 0, tzinfo=timezone('UTC'))
        self._conf2.setDates(sd2, ed2)
        ch.add(self._conf2)

        self._stopDBReq()

    @with_context('database')
    def testAddStorageElements(self):
        """ Tests adding elements to the storage
        """
        storage = getAvatarConferenceStorage()
        self.assertEqual(len(storage), 0)

        addAvatarConference(self._avatar1, self._conf1, "added")
        self.assertEqual(len(storage), 1)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf1.getId()]), 1)
        self.assertEqual(storage[self._avatar1.getId() + '_' + self._conf1.getId()][0]["eventType"], "added")

        addAvatarConference(self._avatar1, self._conf1, "removed")
        self.assertEqual(len(storage), 1)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf1.getId()]), 2)
        self.assertEqual(storage[self._avatar1.getId() + '_' + self._conf1.getId()][1]["eventType"], "removed")

        addAvatarConference(self._avatar1, self._conf2, "added")
        self.assertEqual(len(storage), 2)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf2.getId()]), 1)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf1.getId()]), 2)
        self.assertEqual(storage[self._avatar1.getId() + '_' + self._conf2.getId()][0]["eventType"], "added")

        addAvatarConference(self._avatar2, self._conf1, "added")
        self.assertEqual(len(storage), 3)
        self.assertEqual(len(storage[self._avatar2.getId() + '_' + self._conf1.getId()]), 1)
        self.assertEqual(storage[self._avatar2.getId() + '_' + self._conf1.getId()][0]["eventType"], "added")

        addAvatarConference(self._avatar2, self._conf2, "added")
        self.assertEqual(len(storage), 4)
        self.assertEqual(len(storage[self._avatar2.getId() + '_' + self._conf2.getId()]), 1)
        self.assertEqual(storage[self._avatar2.getId() + '_' + self._conf2.getId()][0]["eventType"], "added")

        addAvatarConference(self._avatar2, self._conf2, "removed")
        self.assertEqual(len(storage), 4)
        self.assertEqual(len(storage[self._avatar2.getId() + '_' + self._conf2.getId()]), 2)
        self.assertEqual(storage[self._avatar2.getId() + '_' + self._conf2.getId()][1]["eventType"], "removed")

        addAvatarConference(self._avatar1, self._conf1, "added")
        addAvatarConference(self._avatar1, self._conf1, "removed")

        self.assertEqual(len(storage), 4)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf1.getId()]), 2)

    @with_context('database')
    def testUpdateConference(self):
        """ Tests if update works properly after making changes in the conference
        """
        storage = getAvatarConferenceStorage()

        participant1 = Participant(self._conf1, self._avatar1)
        participant2 = Participant(self._conf1, self._avatar2)
        participant3 = Participant(self._conf2, self._avatar2)

        self._conf1.getParticipation().addParticipant(participant1)
        self._conf1.getParticipation().addParticipant(participant2)
        self._conf2.getParticipation().addParticipant(participant3)

        self._conf1.setTitle('title')
        self.assertEqual(len(storage), 3)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf1.getId()]), 2)
        self.assertEqual(len(storage[self._avatar2.getId() + '_' + self._conf1.getId()]), 2)
        self.assertEqual(len(storage[self._avatar2.getId() + '_' + self._conf2.getId()]), 1)

        self._conf1.setDescription('description')
        self.assertEqual(len(storage), 3)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf1.getId()]), 2)
        self.assertEqual(len(storage[self._avatar2.getId() + '_' + self._conf1.getId()]), 2)
        self.assertEqual(len(storage[self._avatar2.getId() + '_' + self._conf2.getId()]), 1)

        self._conf2.setTitle('title')
        self.assertEqual(len(storage), 3)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf1.getId()]), 2)
        self.assertEqual(len(storage[self._avatar2.getId() + '_' + self._conf1.getId()]), 2)
        self.assertEqual(len(storage[self._avatar2.getId() + '_' + self._conf2.getId()]), 2)

    @with_context('database')
    def testUpdateParticipantStatus(self):
        """ Tests if update of participant status works properly
        """
        storage = getAvatarConferenceStorage()

        participant1 = Participant(self._conf1, self._avatar1)
        self._conf1.getParticipation().addParticipant(participant1)
        self.assertEqual(len(storage), 1)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf1.getId()]), 1)
        self.assertEqual(storage[self._avatar1.getId() + '_' + self._conf1.getId()][0]["eventType"], "added")

        participant1.setStatusAdded()
        self.assertEqual(len(storage), 1)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf1.getId()]), 1)
        self.assertEqual(storage[self._avatar1.getId() + '_' + self._conf1.getId()][0]["eventType"], "added")

        participant1.setStatusRefused()
        self.assertEqual(len(storage), 1)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf1.getId()]), 2)
        self.assertEqual(storage[self._avatar1.getId() + '_' + self._conf1.getId()][1]["eventType"], "removed")

        participant2 = Participant(self._conf1, self._avatar2)
        participant2.setStatusInvited()
        self.assertEqual(len(storage), 1)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf1.getId()]), 2)

        participant2.setStatusAccepted()
        self.assertEqual(len(storage), 2)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf1.getId()]), 2)
        self.assertEqual(len(storage[self._avatar2.getId() + '_' + self._conf1.getId()]), 1)
        self.assertEqual(storage[self._avatar2.getId() + '_' + self._conf1.getId()][0]["eventType"], "added")

        participant3 = Participant(self._conf2, self._avatar1)
        participant3.setStatusInvited()
        self.assertEqual(len(storage), 2)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf1.getId()]), 2)
        self.assertEqual(len(storage[self._avatar2.getId() + '_' + self._conf1.getId()]), 1)

        participant3.setStatusRejected()
        self.assertEqual(len(storage), 3)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf1.getId()]), 2)
        self.assertEqual(len(storage[self._avatar2.getId() + '_' + self._conf1.getId()]), 1)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf2.getId()]), 1)
        self.assertEqual(storage[self._avatar1.getId() + '_' + self._conf2.getId()][0]["eventType"], "removed")

    @with_context('database')
    def testUpdateRegistrantStatus(self):
        """ Tests if update of registrant status works properly
        """
        storage = getAvatarConferenceStorage()

        registrant1 = Registrant()
        registrant1.setAvatar(self._avatar1)
        registrant1.setEmail("a@a.com")
        self._conf1.addRegistrant(registrant1, self._avatar1)
        self.assertEqual(len(storage), 1)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf1.getId()]), 1)
        self.assertEqual(storage[self._avatar1.getId() + '_' + self._conf1.getId()][0]["eventType"], "added")

        registrant2 = Registrant()
        registrant2.setAvatar(self._avatar2)
        registrant2.setEmail("b@b.com")
        self._conf1.addRegistrant(registrant2, self._avatar2)
        self.assertEqual(len(storage), 2)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf1.getId()]), 1)
        self.assertEqual(len(storage[self._avatar2.getId() + '_' + self._conf1.getId()]), 1)
        self.assertEqual(storage[self._avatar2.getId() + '_' + self._conf1.getId()][0]["eventType"], "added")

        self._conf1.removeRegistrant(registrant2.getId())
        self.assertEqual(len(storage), 2)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf1.getId()]), 1)
        self.assertEqual(len(storage[self._avatar2.getId() + '_' + self._conf1.getId()]), 2)
        self.assertEqual(storage[self._avatar2.getId() + '_' + self._conf1.getId()][1]["eventType"], "removed")

        self._conf1.removeRegistrant(registrant1.getId())
        self.assertEqual(len(storage), 2)
        self.assertEqual(len(storage[self._avatar1.getId() + '_' + self._conf1.getId()]), 2)
        self.assertEqual(len(storage[self._avatar2.getId() + '_' + self._conf1.getId()]), 2)
        self.assertEqual(storage[self._avatar1.getId() + '_' + self._conf1.getId()][1]["eventType"], "removed")

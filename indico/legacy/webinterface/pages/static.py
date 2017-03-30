# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from indico.modules.events.contributions.views import WPAuthorList, WPContributions, WPSpeakerList
from indico.modules.events.layout.views import WPPage
from indico.modules.events.registration.views import WPDisplayRegistrationParticipantList
from indico.modules.events.sessions.views import WPDisplaySession
from indico.modules.events.timetable.views import WPDisplayTimetable
from indico.modules.events.tracks.views import WPDisplayTracks
from indico.legacy.webinterface.pages.conferences import WPConferenceDisplay
from indico.modules.events.views import WPSimpleEventDisplay


class WPStaticEventBase:
    def _getHeader(self):
        return ""

    def _getFooter(self):
        return ""


class WPStaticSimpleEventDisplay(WPStaticEventBase, WPSimpleEventDisplay):
    pass


class WPStaticConferenceDisplay(WPStaticEventBase, WPConferenceDisplay):
    pass


class WPStaticTimetable(WPStaticEventBase, WPDisplayTimetable):
    endpoint = 'timetable.timetable'
    menu_entry_name = 'timetable'


class WPStaticConferenceProgram(WPStaticEventBase, WPDisplayTracks):
    endpoint = 'tracks.program'


class WPStaticDisplayRegistrationParticipantList(WPStaticEventBase, WPDisplayRegistrationParticipantList):
    endpoint = 'event_registration.participant_list'


class WPStaticContributionList(WPStaticEventBase, WPContributions):
    endpoint = 'contributions.contribution_list'
    template_prefix = 'events/contributions/'
    menu_entry_name = 'contributions'


class WPStaticCustomPage(WPStaticEventBase, WPPage):
    pass


class WPStaticAuthorList(WPStaticEventBase, WPAuthorList):
    endpoint = 'contributions.author_list'
    template_prefix = 'events/contributions/'
    menu_entry_name = 'author_index'


class WPStaticSpeakerList(WPStaticEventBase, WPSpeakerList):
    endpoint = 'contributions.speaker_list'
    template_prefix = 'events/contributions/'
    menu_entry_name = 'speaker_index'


class WPStaticSessionDisplay(WPStaticEventBase, WPDisplaySession):
    endpoint = 'sessions.display_session'


class WPStaticContributionDisplay(WPStaticEventBase, WPContributions):
    endpoint = 'contributions.display_contribution'


class WPStaticSubcontributionDisplay(WPStaticEventBase, WPContributions):
    endpoint = 'contributions.display_subcontribution'

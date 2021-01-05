# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.contributions.views import WPAuthorList, WPContributions, WPSpeakerList
from indico.modules.events.layout.views import WPPage
from indico.modules.events.registration.views import WPDisplayRegistrationParticipantList
from indico.modules.events.sessions.views import WPDisplaySession
from indico.modules.events.timetable.views import WPDisplayTimetable
from indico.modules.events.tracks.views import WPDisplayTracks
from indico.modules.events.views import WPConferenceDisplay, WPSimpleEventDisplay


class WPStaticEventBase:
    def _get_header(self):
        return u""

    def _get_footer(self):
        return u""


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

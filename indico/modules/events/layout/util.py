# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals

import binascii
import transaction

from collections import namedtuple
from itertools import chain, count

from indico.core import signals
from indico.core.db import db
from indico.core.plugins import plugin_engine
from indico.modules.events.layout.models.menu import MenuEntry, MenuEntryType
from indico.util.i18n import N_
from indico.util.signals import values_from_signal
from MaKaC.common.cache import GenericCache

MenuEntryData = namedtuple('MenuEntryData', {'title', 'name', 'endpoint', 'visible', 'children', 'plugin'})

DEFAULT_MENU_ENTRIES = [
    MenuEntryData(
        visible=True,
        title=N_("Overview"),
        name='overview',
        endpoint='event.conferenceDisplay-overview',
        children=None,
        plugin=None),
    MenuEntryData(
        visible=True,
        title=N_("Scientific Programme"),
        name='program',
        endpoint='event.conferenceProgram',
        children=[
            MenuEntryData(
                visible=True,
                title=N_("Manage my Tracks"),
                name='program_my_tracks',
                endpoint='event.myconference-myTracks',
                children=None,
                plugin=None),
        ],
        plugin=None),
    MenuEntryData(
        visible=True,
        title=N_("Call for Abstracts"),
        name='call_for_abstracts',
        endpoint='event.conferenceCFA',
        children=[
            MenuEntryData(
                visible=True,
                title=N_("View my Abstracts"),
                name='user_abstracts',
                endpoint='event.userAbstracts',
                children=None,
                plugin=None),
            MenuEntryData(
                visible=True,
                title=N_("Submit Abstract"),
                name='abstract_submission',
                endpoint='event.abstractSubmission',
                children=None,
                plugin=None),
        ],
        plugin=None),
    MenuEntryData(
        visible=True,
        title=N_("Timetable"),
        name='timetable',
        endpoint='event.conferenceTimeTable',
        children=None,
        plugin=None),
    MenuEntryData(
        visible=True,
        title=N_("Contribution List"),
        name='contributions',
        endpoint='event.contributionListDisplay',
        children=None,
        plugin=None),
    MenuEntryData(
        visible=True,
        title=N_("Author List"),
        name='author_index',
        endpoint='event.confAuthorIndex',
        children=None,
        plugin=None),
    MenuEntryData(
        visible=True,
        title=N_("Speaker List"),
        name='speaker_index',
        endpoint='event.confSpeakerIndex',
        children=None,
        plugin=None),
    MenuEntryData(
        visible=True,
        title=N_("My Conference"),
        name='my_conference',
        endpoint='event.myconference',
        children=[
            MenuEntryData(
                visible=True,
                title=N_("My Tracks"),
                endpoint='event.myconference-myTracks',
                name='my_tracks',
                children=None,
                plugin=None),
            MenuEntryData(
                visible=True,
                title=N_("My Sessions"),
                name='my_sessions',
                endpoint='event.myconference-mySessions',
                children=None,
                plugin=None),
            MenuEntryData(
                visible=True,
                title=N_("My Contributions"),
                name='my_contributions',
                endpoint='event.myconference-myContributions',
                children=None,
                plugin=None),
        ],
        plugin=None),
    MenuEntryData(
        visible=True,
        title=N_("Paper Reviewing"),
        name='paper_reviewing',
        endpoint='event.paperReviewingDisplay',
        children=[
            MenuEntryData(
                visible=True,
                title=N_("Manage Paper Reviewing"),
                name='paper_setup',
                endpoint='event_mgmt.confModifReviewing-paperSetup',
                children=None,
                plugin=None),
            MenuEntryData(
                visible=True,
                title=N_("Assign Papers"),
                name='paper_assign',
                endpoint='event_mgmt.assignContributions',
                children=None,
                plugin=None),
            MenuEntryData(
                visible=True,
                title=N_("Referee Area"),
                name='contributions_to_judge',
                endpoint='event_mgmt.confListContribToJudge',
                children=None,
                plugin=None),
            MenuEntryData(
                visible=True,
                title=N_("Content Reviewer Area"),
                name='contributions_as_reviewer',
                endpoint='event_mgmt.confListContribToJudge-asReviewer',
                children=None,
                plugin=None),
            MenuEntryData(
                visible=True,
                title=N_("Layout Reviewer Area"),
                name='contributions_as_editor',
                endpoint='event_mgmt.confListContribToJudge-asEditor',
                children=None,
                plugin=None),
            MenuEntryData(
                visible=True,
                title=N_("Upload Paper"),
                name='paper_upload',
                endpoint='event.paperReviewingDisplay-uploadPaper',
                children=None,
                plugin=None),
            MenuEntryData(
                visible=True,
                title=N_("Download Template"),
                name='download_template',
                endpoint='event.paperReviewingDisplay-downloadTemplate',
                children=None,
                plugin=None),
        ],
        plugin=None),
    MenuEntryData(
        visible=True,
        title=N_("Book of Abstracts"),
        name='abstracts_book',
        endpoint='event.conferenceDisplay-abstractBook',
        children=None,
        plugin=None),
    MenuEntryData(
        visible=True,
        title=N_("Registration"),
        name='registration',
        endpoint='event.confRegistrationFormDisplay',
        children=None,
        plugin=None),
    MenuEntryData(
        visible=True,
        title=N_("Participant List"),
        name='registrants',
        endpoint='event.confRegistrantsDisplay-list',
        children=None,
        plugin=None),
    MenuEntryData(
        visible=True,
        title=N_("Evaluation"),
        name='evaluation',
        endpoint='event.confDisplayEvaluation',
        children=[
            MenuEntryData(
                visible=True,
                title=N_("Evaluation Form"),
                name='evaluation_form',
                endpoint='event.confDisplayEvaluation-display',
                children=None,
                plugin=None),
            MenuEntryData(
                visible=True,
                title=N_("Modify my Evaluation"),
                name='evaluation_edit',
                endpoint='event.confDisplayEvaluation-modif',
                children=None,
                plugin=None),
        ],
        plugin=None)
]

_cache = GenericCache('updated-menus')


def menu_entries_for_event(event):
    entries = MenuEntry.find(event_id=event.getId(), parent_id=None).order_by(MenuEntry.position.asc()).all()

    plugin_key = ','.join(sorted(plugin_engine.get_active_plugins()))
    cache_key = binascii.crc32(plugin_key) & 0xffffffff
    processed = _cache.get(cache_key)

    if not processed:
        # menu entries from signal
        pos_gen = count(start=entries[-1].position + 1)
        existing = ((entry.endpoint, entry.type)
                    for entry in entries
                    if entry.type in {MenuEntryType.internal_link, MenuEntryType.plugin_link})
        signal_entries = (_build_entry(event, entry_data)
                          for entry_data in values_from_signal(signals.event.sidemenu.send())
                          if (entry_data.endpoint,
                              MenuEntryType.plugin_link if entry_data.plugin else MenuEntryType.internal_link)
                          in existing)
        for position, entry in zip(pos_gen, signal_entries):
            entry.position = position
        entries.extend(signal_entries)
        _cache.set(cache_key, True)
        transaction.commit()

    # Filter out entries from disabled plugins
    plugins = plugin_engine.get_active_plugins().viewkeys()
    return (entry for entry in entries if entry.type != MenuEntryType.plugin_link or entry.plugin in plugins)


def default_menu_entries(event):
    entries = (_build_entry(event, entry_data, i) for i, entry_data in
               enumerate(chain(DEFAULT_MENU_ENTRIES, values_from_signal(signals.event.sidemenu.send()))))
    db.session.add_all(entries)
    transaction.commit()
    return entries


def _build_entry(event, data, position=0):
    entry = MenuEntry(
        event_id=event.getId(),
        visible=data.visible(event) if hasattr(data.visible, '__call__') else data.visible,
        title=data.title,
        name=data.name,
        endpoint=data.endpoint,
        position=position,
        children=[_build_entry(event, entry_data, i) for i, entry_data in enumerate(data.children or [])]
    )

    if data.plugin:
        entry.type = MenuEntryType.plugin_link
        entry.plugin = data.plugin
    else:
        entry.type = MenuEntryType.internal_link

    return entry


def move_entry(entry, to):
    from_ = entry.position
    new_pos = to
    value = -1
    if to is None or to < 0:
        new_pos = to = -1

    if from_ > to:
        new_pos += 1
        from_, to = to, from_
        to -= 1
        value = 1

    entries = MenuEntry.find(MenuEntry.parent_id == entry.parent_id,
                             MenuEntry.event_id == entry.event_id,
                             MenuEntry.position.between(from_ + 1, to))
    for e in entries:
        e.position += value
    entry.position = new_pos

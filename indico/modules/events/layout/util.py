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

from itertools import chain, count

from indico.core import signals
from indico.core.plugins import plugin_engine, url_for_plugin
from indico.modules.events.layout.models.menu import MenuEntry, MenuEntryType
from indico.util.i18n import N_
from indico.util.signals import values_from_signal
from indico.web.flask.util import url_for

DEFAULT_MENU_ENTRIES = [{
    'visible': True,
    'title': N_("Overview"),
    'endpoint': 'event.conferenceDisplay-overview'
}, {
    'visible': True,
    'title': N_("Scientific Programme"),
    'endpoint': 'event.conferenceProgram',
    'children': [{
        'visible': True,
        'title': N_("Manage my Tracks"),
        'endpoint': 'event.myconference-myTracks'
    }],
}, {
    'visible': True,
    'title': N_("Call for Abstracts"),
    'endpoint': 'event.conferenceCFA',
    'children': [{
        'visible': True,
        'title': N_("View my Abstracts"),
        'endpoint': 'event.userAbstracts'
    }, {
        'visible': True,
        'title': N_("Submit Abstract"),
        'endpoint': 'event.abstractSubmission'
    }]
}, {
    'visible': True,
    'title': N_("Timetable"),
    'endpoint': 'event.conferenceTimeTable'
}, {
    'visible': True,
    'title': N_("Contribution List"),
    'endpoint': 'event.contributionListDisplay'
}, {
    'visible': True,
    'title': N_("Author List"),
    'endpoint': 'event.confAuthorIndex'
}, {
    'visible': True,
    'title': N_("Speaker List"),
    'endpoint': 'event.confSpeakerIndex'
}, {
    'visible': True,
    'title': N_("My Conference"),
    'endpoint': 'event.myconference',
    'children': [{
        'visible': True,
        'title': N_("My Tracks"),
        'endpoint': 'event.myconference-myTracks'
    }, {
        'visible': True,
        'title': N_("My Sessions"),
        'endpoint': 'event.myconference-mySessions'
    }, {
        'visible': True,
        'title': N_("My Contributions"),
        'endpoint': 'event.myconference-myContributions'
    }]
}, {
    'visible': True,
    'title': N_("Paper Reviewing"),
    'endpoint': 'event.paperReviewingDisplay',
    'children': [{
        'visible': True,
        'title': N_("Manage Paper Reviewing"),
        'endpoint': 'event_mgmt.confModifReviewing-paperSetup'
    }, {
        'visible': True,
        'title': N_("Assign Papers"),
        'endpoint': 'event_mgmt.assignContributions'
    }, {
        'visible': True,
        'title': N_("Referee Area"),
        'endpoint': 'event_mgmt.confListContribToJudge'
    }, {
        'visible': True,
        'title': N_("Content Reviewer Area"),
        'endpoint': 'event_mgmt.confListContribToJudge-asReviewer'
    }, {
        'visible': True,
        'title': N_("Layout Reviewer Area"),
        'endpoint': 'event_mgmt.confListContribToJudge-asEditor'
    }, {
        'visible': True,
        'title': N_("Upload Paper"),
        'endpoint': 'event.paperReviewingDisplay-uploadPaper'
    }, {
        'visible': True,
        'title': N_("Download Template"),
        'endpoint': 'event.paperReviewingDisplay-downloadTemplate'
    }],
}, {
    'visible': True,
    'title': N_("Book of Abstracts"),
    'endpoint': 'event.conferenceDisplay-abstractBook'
}, {
    'visible': True,
    'title': N_("Registration"),
    'endpoint': 'event.confRegistrationFormDisplay'
}, {
    'visible': True,
    'title': N_("Participant List"),
    'endpoint': 'event.confRegistrantsDisplay-list'
}, {
    'visible': True,
    'title': N_("Evaluation"),
    'endpoint': 'event.confDisplayEvaluation',
    'children': [{
        'visible': True,
        'title': N_("Evaluation Form"),
        'endpoint': 'event.confDisplayEvaluation-display'
    }, {
        'visible': True,
        'title': N_("Modify my Evaluation"),
        'endpoint': 'event.confDisplayEvaluation-modif'
    }]
}]


def menu_entries_for_event(event):
    entries = MenuEntry.find(event_id=event.getId(), parent=None).order_by(MenuEntry.position.desc()).all()
    pos_gen = count(start=entries[-1].position + 1)

    # menu entries from newly enabled plugins
    existing_plugins = (entry.plugin for entry in entries if entry.type == MenuEntryType.plugin_link)
    new_plugin_entries = (_build_entry(event, entry_data)
                          for i, entry_data in enumerate(values_from_signal(signals.event.sidemenu.send()))
                          if entry_data['plugin'] not in existing_plugins)
    for position, entry in zip(pos_gen, new_plugin_entries):
        entry.position = position
    entries.extend(new_plugin_entries)
    plugins = plugin_engine.get_active_plugins().viewvalues()
    return (entry for entry in entries if entry.type != MenuEntryType.plugin_link or entry.plugin in plugins)


def default_menu_entries(event):
    return (_build_entry(event, entry_data, i) for i, entry_data in
            enumerate(chain(DEFAULT_MENU_ENTRIES, values_from_signal(signals.event.sidemenu.send()))))


def _build_entry(event, data, position=0):
    entry = MenuEntry(
        event_id=event.getId(),
        visible=data['visible'],
        title=data['title'],
        position=position,
        children=[_build_entry(event, entry_data, i) for i, entry_data in enumerate(data.get('children', []))]
    )

    if 'plugin' in data:
        entry.link = url_for_plugin(data['endpoint'], event)
        entry.type = MenuEntryType.plugin_link
        entry.plugin = data['plugin']
    else:
        entry.link = url_for(data['endpoint'], event)
        entry.type = MenuEntryType.internal_link

    return entry

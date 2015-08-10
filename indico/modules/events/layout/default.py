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

from indico.modules.events.layout.util import MenuEntryData
from indico.util.i18n import N_

DEFAULT_MENU_ENTRIES = [
    MenuEntryData(
        visible=True,
        title=N_("Overview"),
        name='overview',
        endpoint='event.conferenceDisplay-overview',
        children=None,
    ),
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
            ),
        ],
    ),
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
            ),
            MenuEntryData(
                visible=True,
                title=N_("Submit Abstract"),
                name='abstract_submission',
                endpoint='event.abstractSubmission',
                children=None,
            ),
        ],
    ),
    MenuEntryData(
        visible=True,
        title=N_("Timetable"),
        name='timetable',
        endpoint='event.conferenceTimeTable',
        children=None,
    ),
    MenuEntryData(
        visible=True,
        title=N_("Contribution List"),
        name='contributions',
        endpoint='event.contributionListDisplay',
        children=None,
    ),
    MenuEntryData(
        visible=True,
        title=N_("Author List"),
        name='author_index',
        endpoint='event.confAuthorIndex',
        children=None,
    ),
    MenuEntryData(
        visible=False,
        title=N_("Speaker List"),
        name='speaker_index',
        endpoint='event.confSpeakerIndex',
        children=None,
    ),
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
            ),
            MenuEntryData(
                visible=True,
                title=N_("My Sessions"),
                name='my_sessions',
                endpoint='event.myconference-mySessions',
                children=None,
            ),
            MenuEntryData(
                visible=True,
                title=N_("My Contributions"),
                name='my_contributions',
                endpoint='event.myconference-myContributions',
                children=None,
            ),
        ],
    ),
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
            ),
            MenuEntryData(
                visible=True,
                title=N_("Assign Papers"),
                name='paper_assign',
                endpoint='event_mgmt.assignContributions',
                children=None,
            ),
            MenuEntryData(
                visible=True,
                title=N_("Referee Area"),
                name='contributions_to_judge',
                endpoint='event_mgmt.confListContribToJudge',
                children=None,
            ),
            MenuEntryData(
                visible=True,
                title=N_("Content Reviewer Area"),
                name='contributions_as_reviewer',
                endpoint='event_mgmt.confListContribToJudge-asReviewer',
                children=None,
            ),
            MenuEntryData(
                visible=True,
                title=N_("Layout Reviewer Area"),
                name='contributions_as_editor',
                endpoint='event_mgmt.confListContribToJudge-asEditor',
                children=None,
            ),
            MenuEntryData(
                visible=True,
                title=N_("Upload Paper"),
                name='paper_upload',
                endpoint='event.paperReviewingDisplay-uploadPaper',
                children=None,
            ),
            MenuEntryData(
                visible=True,
                title=N_("Download Template"),
                name='download_template',
                endpoint='event.paperReviewingDisplay-downloadTemplate',
                children=None,
            ),
        ],
    ),
    MenuEntryData(
        visible=True,
        title=N_("Book of Abstracts"),
        name='abstracts_book',
        endpoint='event.conferenceDisplay-abstractBook',
        children=None,
    ),
    MenuEntryData(
        visible=True,
        title=N_("Registration"),
        name='registration',
        endpoint='event.confRegistrationFormDisplay',
        children=None,
    ),
    MenuEntryData(
        visible=False,
        title=N_("Participant List"),
        name='registrants',
        endpoint='event.confRegistrantsDisplay-list',
        children=None,
    ),
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
            ),
            MenuEntryData(
                visible=True,
                title=N_("Modify my Evaluation"),
                name='evaluation_edit',
                endpoint='event.confDisplayEvaluation-modif',
                children=None,
            ),
        ],
    )
]

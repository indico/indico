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

from flask import session

from indico.modules.events.layout.util import MenuEntryData
from indico.util.i18n import N_
from MaKaC.paperReviewing import ConferencePaperReview


def _visibility_my_tracks(event):
    return event.getAbstractMgr().isActive() and event.getCoordinatedTracks(session.user.as_avatar)


def _visibility_call_for_abstracts(event):
    return event.getAbstractMgr().isActive() and event.hasEnabledSection('cfa')


def _visibility_my_conference(event):
    return session.user is not None


def _visibility_abstracts_book(event):
    return event.getAbstractMgr().isActive() and event.hasEnabledSection('cfa')


def _visibility_my_contributions(event):
    return event.getContribsForSubmitter(session.user.as_avatar)


def _visibility_paper_review(event):
    return event.getConfPaperReview().hasReviewing()


def _visibility_paper_review_transfer(event):
    return _visibility_paper_review(event) and event.getContribsForSubmitter(session.user.as_avatar)


def _visibility_role(event, role):
    user = session.user
    if user is None:
        return False

    roles = user.get_linked_roles('conference')
    return role in roles and event in user.get_linked_objects('conference', role)


def _visibility_paper_review_managment(event):
    return _visibility_role('paperReviewManager')


def _visibility_registration(event):
    return event.getRegistrationForm().isActivated() and event.hasEnabledSection('regForm')


def _visibility_judge(event):
    return (_visibility_role(event, 'referee')
            and (event.getConfPaperReview().getChoice() == ConferencePaperReview.CONTENT_REVIEWING
                 or event.getConfPaperReview().getChoice() == ConferencePaperReview.CONTENT_AND_LAYOUT_REVIEWING))


def _visibility_contributions_as_reviewer(event):
    return (_visibility_role(event, 'reviewer')
            and (event.getConfPaperReview().getChoice() == ConferencePaperReview.CONTENT_REVIEWING
                 or event.getConfPaperReview().getChoice() == ConferencePaperReview.CONTENT_AND_LAYOUT_REVIEWING))


def _visibility_contributions_as_editor(event):
    return (_visibility_role(event, 'editor')
            and (event.getConfPaperReview().getChoice() == ConferencePaperReview.CONTENT_REVIEWING
                 or event.getConfPaperReview().getChoice() == ConferencePaperReview.CONTENT_AND_LAYOUT_REVIEWING))


def _visibility_paper_assign(event):
    return _visibility_paper_review_managment(event) and _visibility_judge(event)


DEFAULT_MENU_ENTRIES = [
    MenuEntryData(
        title=N_("Overview"),
        name='overview',
        endpoint='event.conferenceDisplay-overview',
        children=None,
    ),
    MenuEntryData(
        title=N_("Scientific Programme"),
        name='program',
        endpoint='event.conferenceProgram',
        children=[
            MenuEntryData(
                title=N_("Manage my Tracks"),
                name='program_my_tracks',
                visible=_visibility_my_tracks,
                endpoint='event.myconference-myTracks',
                children=None,
            ),
        ],
    ),
    MenuEntryData(
        title=N_("Call for Abstracts"),
        name='call_for_abstracts',
        visible=_visibility_call_for_abstracts,
        endpoint='event.conferenceCFA',
        children=[
            MenuEntryData(
                title=N_("View my Abstracts"),
                name='user_abstracts',
                endpoint='event.userAbstracts',
                children=None,
            ),
            MenuEntryData(
                title=N_("Submit Abstract"),
                name='abstract_submission',
                endpoint='event.abstractSubmission',
                children=None,
            ),
        ],
    ),
    MenuEntryData(
        title=N_("Timetable"),
        name='timetable',
        endpoint='event.conferenceTimeTable',
        children=None,
    ),
    MenuEntryData(
        title=N_("Contribution List"),
        name='contributions',
        endpoint='event.contributionListDisplay',
        children=None,
    ),
    MenuEntryData(
        title=N_("Author List"),
        name='author_index',
        visible_default=False,
        endpoint='event.confAuthorIndex',
        children=None,
    ),
    MenuEntryData(
        title=N_("Speaker List"),
        name='speaker_index',
        visible_default=False,
        endpoint='event.confSpeakerIndex',
        children=None,
    ),
    MenuEntryData(
        title=N_("My Conference"),
        name='my_conference',
        visible=_visibility_my_conference,
        endpoint='event.myconference',
        children=[
            MenuEntryData(
                title=N_("My Tracks"),
                endpoint='event.myconference-myTracks',
                visible=_visibility_my_tracks,
                name='my_tracks',
                children=None,
            ),
            MenuEntryData(
                title=N_("My Sessions"),
                name='my_sessions',
                endpoint='event.myconference-mySessions',
                children=None,
            ),
            MenuEntryData(
                title=N_("My Contributions"),
                name='my_contributions',
                visible=_visibility_my_contributions,
                endpoint='event.myconference-myContributions',
                children=None,
            ),
        ],
    ),
    MenuEntryData(
        title=N_("Paper Reviewing"),
        name='paper_reviewing',
        visible=_visibility_paper_review,
        endpoint='event.paperReviewingDisplay',
        children=[
            MenuEntryData(
                title=N_("Manage Paper Reviewing"),
                name='paper_setup',
                visible=_visibility_paper_review_managment,
                endpoint='event_mgmt.confModifReviewing-paperSetup',
                children=None,
            ),
            MenuEntryData(
                title=N_("Assign Papers"),
                name='paper_assign',
                visible=_visibility_paper_assign,
                endpoint='event_mgmt.assignContributions',
                children=None,
            ),
            MenuEntryData(
                title=N_("Referee Area"),
                name='contributions_to_judge',
                visible=_visibility_judge,
                endpoint='event_mgmt.confListContribToJudge',
                children=None,
            ),
            MenuEntryData(
                title=N_("Content Reviewer Area"),
                name='contributions_as_reviewer',
                visible=_visibility_contributions_as_reviewer,
                endpoint='event_mgmt.confListContribToJudge-asReviewer',
                children=None,
            ),
            MenuEntryData(
                title=N_("Layout Reviewer Area"),
                name='contributions_as_editor',
                visible=_visibility_contributions_as_editor,
                endpoint='event_mgmt.confListContribToJudge-asEditor',
                children=None,
            ),
            MenuEntryData(
                title=N_("Upload Paper"),
                name='paper_upload',
                visible=_visibility_paper_review_transfer,
                endpoint='event.paperReviewingDisplay-uploadPaper',
                children=None,
            ),
            MenuEntryData(
                title=N_("Download Template"),
                name='download_template',
                visible=_visibility_paper_review_transfer,
                endpoint='event.paperReviewingDisplay-downloadTemplate',
                children=None,
            ),
        ],
    ),
    MenuEntryData(
        title=N_("Book of Abstracts"),
        name='abstracts_book',
        visible=_visibility_abstracts_book,
        endpoint='event.conferenceDisplay-abstractBook',
        children=None,
    ),
    MenuEntryData(
        title=N_("Registration"),
        name='registration',
        visible=_visibility_registration,
        endpoint='event.confRegistrationFormDisplay',
        children=None,
    ),
    MenuEntryData(
        title=N_("Participant List"),
        name='registrants',
        visible=_visibility_registration,
        endpoint='event.confRegistrantsDisplay-list',
        children=None,
    ),
    MenuEntryData(
        title=N_("Evaluation"),
        name='evaluation',
        endpoint='event.confDisplayEvaluation',
        children=[
            MenuEntryData(
                title=N_("Evaluation Form"),
                name='evaluation_form',
                endpoint='event.confDisplayEvaluation-display',
                children=None,
            ),
            MenuEntryData(
                title=N_("Modify my Evaluation"),
                name='evaluation_edit',
                endpoint='event.confDisplayEvaluation-modif',
                children=None,
            ),
        ],
    )
]

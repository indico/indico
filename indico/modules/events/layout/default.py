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

from flask import session

from indico.modules.events.layout.util import MenuEntryData
from indico.util.i18n import N_
from MaKaC.paperReviewing import ConferencePaperReview


def _visibility_my_tracks(event):
    return bool(event.getAbstractMgr().isActive() and event.getCoordinatedTracks(session.avatar))


def _visibility_call_for_abstracts(event):
    return event.getAbstractMgr().isActive() and event.hasEnabledSection('cfa')


def _visibility_my_conference(event):
    return session.user is not None


def _visibility_abstracts_book(event):
    return event.getAbstractMgr().isActive() and event.hasEnabledSection('cfa')


def _visibility_my_contributions(event):
    return event.getContribsForSubmitter(session.avatar)


def _visibility_paper_review(event):
    return event.getConfPaperReview().hasReviewing()


def _visibility_paper_review_transfer(event):
    return bool(_visibility_paper_review(event) and event.getContribsForSubmitter(session.avatar))


def _visibility_role(event, role):
    user = session.user
    if user is None:
        return False

    roles = user.get_linked_roles('conference')
    return role in roles and event in user.get_linked_objects('conference', role)


def _visibility_paper_review_managment(event):
    return _visibility_role(event, 'paperReviewManager')


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
        position=0,
        static_site=True
    ),
    MenuEntryData(
        title=N_("Scientific Programme"),
        name='program',
        endpoint='event.conferenceProgram',
        position=1,
        static_site=True
    ),
    MenuEntryData(
        title=N_("Manage my Tracks"),
        name='program_my_tracks',
        visible=_visibility_my_tracks,
        endpoint='event.myconference-myTracks',
        parent='program',
    ),
    MenuEntryData(
        title=N_("Call for Abstracts"),
        name='call_for_abstracts',
        endpoint='event.conferenceCFA',
        position=2,
        visible=_visibility_call_for_abstracts,
    ),
    MenuEntryData(
        title=N_("View my Abstracts"),
        name='user_abstracts',
        endpoint='event.userAbstracts',
        position=0,
        parent='call_for_abstracts'
    ),
    MenuEntryData(
        title=N_("Submit Abstract"),
        name='abstract_submission',
        endpoint='event.abstractSubmission',
        position=1,
        parent='call_for_abstracts'
    ),
    MenuEntryData(
        title=N_("Timetable"),
        name='timetable',
        endpoint='event.conferenceTimeTable',
        position=3,
        static_site=True
    ),
    MenuEntryData(
        title=N_("Contribution List"),
        name='contributions',
        endpoint='event.contributionListDisplay',
        position=4,
        static_site=True
    ),
    MenuEntryData(
        title=N_("Author List"),
        name='author_index',
        endpoint='event.confAuthorIndex',
        position=5,
        is_enabled=False,
        static_site=True
    ),
    MenuEntryData(
        title=N_("Speaker List"),
        name='speaker_index',
        endpoint='event.confSpeakerIndex',
        position=6,
        is_enabled=False,
        static_site=True
    ),
    MenuEntryData(
        title=N_("My Conference"),
        name='my_conference',
        endpoint='event.myconference',
        position=7,
        visible=_visibility_my_conference
    ),
    MenuEntryData(
        title=N_("My Tracks"),
        endpoint='event.myconference-myTracks',
        name='my_tracks',
        visible=_visibility_my_tracks,
        position=0,
        parent='my_conference'
    ),
    MenuEntryData(
        title=N_("My Sessions"),
        name='my_sessions',
        endpoint='event.myconference-mySessions',
        position=1,
        parent='my_conference'
    ),
    MenuEntryData(
        title=N_("My Contributions"),
        name='my_contributions',
        visible=_visibility_my_contributions,
        endpoint='event.myconference-myContributions',
        position=2,
        parent='my_conference'
    ),
    MenuEntryData(
        title=N_("Paper Reviewing"),
        name='paper_reviewing',
        endpoint='event.paperReviewingDisplay',
        position=8,
        visible=_visibility_paper_review
    ),
    MenuEntryData(
        title=N_("Manage Paper Reviewing"),
        name='paper_setup',
        endpoint='event_mgmt.confModifReviewing-paperSetup',
        visible=_visibility_paper_review_managment,
        position=0,
        parent='paper_reviewing'
    ),
    MenuEntryData(
        title=N_("Assign Papers"),
        name='paper_assign',
        endpoint='event_mgmt.assignContributions',
        visible=_visibility_paper_assign,
        position=1,
        parent='paper_reviewing'
    ),
    MenuEntryData(
        title=N_("Referee Area"),
        name='contributions_to_judge',
        endpoint='event_mgmt.confListContribToJudge',
        visible=_visibility_judge,
        position=2,
        parent='paper_reviewing'
    ),
    MenuEntryData(
        title=N_("Content Reviewer Area"),
        name='contributions_as_reviewer',
        endpoint='event_mgmt.confListContribToJudge-asReviewer',
        visible=_visibility_contributions_as_reviewer,
        position=3,
        parent='paper_reviewing'
    ),
    MenuEntryData(
        title=N_("Layout Reviewer Area"),
        name='contributions_as_editor',
        endpoint='event_mgmt.confListContribToJudge-asEditor',
        visible=_visibility_contributions_as_editor,
        position=4,
        parent='paper_reviewing'
    ),
    MenuEntryData(
        title=N_("Upload Paper"),
        name='paper_upload',
        endpoint='event.paperReviewingDisplay-uploadPaper',
        visible=_visibility_paper_review_transfer,
        position=5,
        parent='paper_reviewing'
    ),
    MenuEntryData(
        title=N_("Download Template"),
        name='download_template',
        endpoint='event.paperReviewingDisplay-downloadTemplate',
        visible=_visibility_paper_review_transfer,
        position=6,
        parent='paper_reviewing'
    ),
    MenuEntryData(
        title=N_("Book of Abstracts"),
        name='abstracts_book',
        endpoint='event.conferenceDisplay-abstractBook',
        position=9,
        visible=_visibility_abstracts_book,
        static_site='files/generatedPdf/BookOfAbstracts.pdf'
    ),
    MenuEntryData(
        title=N_("Registration"),
        name='registration',
        endpoint='event.confRegistrationFormDisplay',
        position=10,
        visible=_visibility_registration
    ),
    MenuEntryData(
        title=N_("Participant List"),
        name='registrants',
        endpoint='event.confRegistrantsDisplay-list',
        position=11,
        visible=_visibility_registration,
        static_site=True
    ),
    MenuEntryData(
        title=N_("Evaluation"),
        name='evaluation',
        endpoint='event.confDisplayEvaluation',
        position=12
    ),
    MenuEntryData(
        title=N_("Evaluation Form"),
        name='evaluation_form',
        endpoint='event.confDisplayEvaluation-display',
        position=0,
        parent='evaluation'
    ),
    MenuEntryData(
        title=N_("Modify my Evaluation"),
        name='evaluation_edit',
        endpoint='event.confDisplayEvaluation-modif',
        position=1,
        parent='evaluation'
    )
]

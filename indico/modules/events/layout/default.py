# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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
from indico.util.i18n import _
from MaKaC.paperReviewing import ConferencePaperReview


def _visibility_my_tracks(event):
    return bool(event.getAbstractMgr().isActive() and event.getCoordinatedTracks(session.avatar))


def _visibility_call_for_abstracts(event):
    return event.getAbstractMgr().isActive() and event.hasEnabledSection('cfa')


def _visibility_my_conference(event):
    return session.user is not None


def _visibility_abstracts_book(event):
    return event.getAbstractMgr().isActive() and event.hasEnabledSection('cfa')


def _visibility_paper_review(event):
    return event.getConfPaperReview().hasReviewing()


def _visibility_paper_review_transfer(event):
    return bool(_visibility_paper_review(event) and
                any(c for c in event.as_event.contributions if c.can_manage(session.user, 'submit')))


def _visibility_role(event, role):
    user = session.user
    if user is None:
        return False

    roles = user.get_linked_roles('conference')
    return role in roles and event in user.get_linked_objects('conference', role)


def _visibility_paper_review_managment(event):
    return _visibility_role(event, 'paperReviewManager')


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


def get_default_menu_entries():
    return [
        MenuEntryData(
            title=_("Overview"),
            name='overview',
            endpoint='event.conferenceDisplay-overview',
            position=0,
            static_site=True
        ),
        MenuEntryData(
            title=_("Scientific Programme"),
            name='program',
            endpoint='event.conferenceProgram',
            position=1,
            static_site=True
        ),
        MenuEntryData(
            title=_("Manage my Tracks"),
            name='program_my_tracks',
            visible=_visibility_my_tracks,
            endpoint='event.myconference-myTracks',
            parent='program',
        ),
        MenuEntryData(
            title=_("Call for Abstracts"),
            name='call_for_abstracts',
            endpoint='event.conferenceCFA',
            position=2,
            visible=_visibility_call_for_abstracts,
        ),
        MenuEntryData(
            title=_("View my Abstracts"),
            name='user_abstracts',
            endpoint='event.userAbstracts',
            position=0,
            parent='call_for_abstracts'
        ),
        MenuEntryData(
            title=_("Submit Abstract"),
            name='abstract_submission',
            endpoint='event.abstractSubmission',
            position=1,
            parent='call_for_abstracts'
        ),
        MenuEntryData(
            title=_("My Conference"),
            name='my_conference',
            endpoint='event.myconference',
            position=7,
            visible=_visibility_my_conference
        ),
        MenuEntryData(
            title=_("My Tracks"),
            endpoint='event.myconference-myTracks',
            name='my_tracks',
            visible=_visibility_my_tracks,
            position=0,
            parent='my_conference'
        ),
        MenuEntryData(
            title=_("Paper Reviewing"),
            name='paper_reviewing',
            endpoint='event.paperReviewingDisplay',
            position=8,
            visible=_visibility_paper_review
        ),
        MenuEntryData(
            title=_("Manage Paper Reviewing"),
            name='paper_setup',
            endpoint='event_mgmt.confModifReviewing-paperSetup',
            visible=_visibility_paper_review_managment,
            position=0,
            parent='paper_reviewing'
        ),
        MenuEntryData(
            title=_("Assign Papers"),
            name='paper_assign',
            endpoint='event_mgmt.assignContributions',
            visible=_visibility_paper_assign,
            position=1,
            parent='paper_reviewing'
        ),
        MenuEntryData(
            title=_("Referee Area"),
            name='contributions_to_judge',
            endpoint='event_mgmt.confListContribToJudge',
            visible=_visibility_judge,
            position=2,
            parent='paper_reviewing'
        ),
        MenuEntryData(
            title=_("Content Reviewer Area"),
            name='contributions_as_reviewer',
            endpoint='event_mgmt.confListContribToJudge-asReviewer',
            visible=_visibility_contributions_as_reviewer,
            position=3,
            parent='paper_reviewing'
        ),
        MenuEntryData(
            title=_("Layout Reviewer Area"),
            name='contributions_as_editor',
            endpoint='event_mgmt.confListContribToJudge-asEditor',
            visible=_visibility_contributions_as_editor,
            position=4,
            parent='paper_reviewing'
        ),
        MenuEntryData(
            title=_("Upload Paper"),
            name='paper_upload',
            endpoint='event.paperReviewingDisplay-uploadPaper',
            visible=_visibility_paper_review_transfer,
            position=5,
            parent='paper_reviewing'
        ),
        MenuEntryData(
            title=_("Download Template"),
            name='download_template',
            endpoint='event.paperReviewingDisplay-downloadTemplate',
            visible=_visibility_paper_review_transfer,
            position=6,
            parent='paper_reviewing'
        ),
        MenuEntryData(
            title=_("Book of Abstracts"),
            name='abstracts_book',
            endpoint='event.conferenceDisplay-abstractBook',
            position=9,
            visible=_visibility_abstracts_book,
            static_site='files/generatedPdf/BookOfAbstracts.pdf'
        )
    ]

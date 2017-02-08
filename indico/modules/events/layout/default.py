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

from __future__ import unicode_literals

from flask import session

from indico.modules.events.layout.util import MenuEntryData, get_menu_entry_by_name
from indico.modules.events.contributions.util import has_contributions_with_user_as_submitter
from indico.util.i18n import _


def _visibility_my_conference(event):
    return session.user and (get_menu_entry_by_name('my_contributions', event).is_visible or
                             get_menu_entry_by_name('my_sessions', event).is_visible)


def _visibility_paper_review(event):
    return event.as_legacy.getConfPaperReview().hasReviewing()


def _visibility_paper_review_transfer(event):
    return (session.user and _visibility_paper_review(event) and
            has_contributions_with_user_as_submitter(event, session.user))


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
            title=_("My Conference"),
            name='my_conference',
            endpoint='event.myconference',
            position=7,
            visible=_visibility_my_conference
        ),
        MenuEntryData(
            title=_("Paper Reviewing (old)"),
            name='paper_reviewing_old',
            endpoint='event.paperReviewingDisplay',
            position=8,
            visible=_visibility_paper_review
        ),
        MenuEntryData(
            title=_("Manage Paper Reviewing"),
            name='paper_setup',
            endpoint='event_mgmt.confModifReviewing-paperSetup',
            visible=_visibility_paper_review,
            position=0,
            parent='paper_reviewing_old'
        ),
        MenuEntryData(
            title=_("Assign Papers"),
            name='paper_assign',
            endpoint='event_mgmt.assignContributions',
            visible=_visibility_paper_review,
            position=1,
            parent='paper_reviewing_old'
        ),
        MenuEntryData(
            title=_("Referee Area"),
            name='contributions_to_judge',
            endpoint='event_mgmt.confListContribToJudge',
            visible=_visibility_paper_review,
            position=2,
            parent='paper_reviewing_old'
        ),
        MenuEntryData(
            title=_("Content Reviewer Area"),
            name='contributions_as_reviewer',
            endpoint='event_mgmt.confListContribToJudge-asReviewer',
            visible=_visibility_paper_review,
            position=3,
            parent='paper_reviewing_old'
        ),
        MenuEntryData(
            title=_("Layout Reviewer Area"),
            name='contributions_as_editor',
            endpoint='event_mgmt.confListContribToJudge-asEditor',
            visible=_visibility_paper_review,
            position=4,
            parent='paper_reviewing_old'
        ),
        MenuEntryData(
            title=_("Upload Paper"),
            name='paper_upload',
            endpoint='event.paperReviewingDisplay-uploadPaper',
            visible=_visibility_paper_review_transfer,
            position=5,
            parent='paper_reviewing_old'
        ),
        MenuEntryData(
            title=_("Download Template"),
            name='download_template',
            endpoint='event.paperReviewingDisplay-downloadTemplate',
            visible=_visibility_paper_review_transfer,
            position=6,
            parent='paper_reviewing_old'
        )
    ]

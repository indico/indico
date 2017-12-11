# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from flask import render_template, session

from indico.modules.events.abstracts.util import filter_field_values, get_visible_reviewed_for_tracks
from indico.modules.events.contributions.models.fields import ContributionFieldVisibility
from indico.modules.events.management.views import WPEventManagement
from indico.modules.events.views import WPConferenceDisplayBase
from indico.util.mathjax import MathjaxMixin


class WPManageAbstracts(MathjaxMixin, WPEventManagement):
    template_prefix = 'events/abstracts/'
    sidemenu_option = 'abstracts'

    def getJSFiles(self):
        return (WPEventManagement.getJSFiles(self) +
                self._asset_env['markdown_js'].urls() +
                self._asset_env['selectize_js'].urls() +
                self._asset_env['modules_reviews_js'].urls() +
                self._asset_env['modules_abstracts_js'].urls())

    def getCSSFiles(self):
        return WPEventManagement.getCSSFiles(self) + self._asset_env['selectize_css'].urls()

    def _getHeadContent(self):
        return WPEventManagement._getHeadContent(self) + MathjaxMixin._getHeadContent(self)


class WPDisplayAbstractsBase(WPConferenceDisplayBase):
    template_prefix = 'events/abstracts/'

    def getJSFiles(self):
        return (WPConferenceDisplayBase.getJSFiles(self) +
                self._asset_env['markdown_js'].urls() +
                self._asset_env['selectize_js'].urls() +
                self._asset_env['modules_reviews_js'].urls() +
                self._asset_env['modules_abstracts_js'].urls())

    def getCSSFiles(self):
        return WPConferenceDisplayBase.getCSSFiles(self) + self._asset_env['selectize_css'].urls()


class WPDisplayAbstracts(WPDisplayAbstractsBase):
    menu_entry_name = 'call_for_abstracts'


class WPDisplayCallForAbstracts(WPDisplayAbstracts):
    def getJSFiles(self):
        return WPDisplayAbstractsBase.getJSFiles(self) + self._asset_env['modules_event_display_js'].urls()


class WPDisplayAbstractsReviewing(WPDisplayAbstracts):
    menu_entry_name = 'abstract_reviewing_area'

    def getJSFiles(self):
        return WPDisplayAbstracts.getJSFiles(self) + self._asset_env['modules_event_management_js'].urls()


def render_abstract_page(abstract, view_class=None, management=False):
    from indico.modules.events.abstracts.forms import (AbstractCommentForm, AbstractJudgmentForm,
                                                       AbstractReviewedForTracksForm, build_review_form)
    comment_form = AbstractCommentForm(abstract=abstract, user=session.user, formdata=None)
    review_form = None
    reviewed_for_tracks = list(abstract.get_reviewed_for_groups(session.user))
    if len(reviewed_for_tracks) == 1:
        review_form = build_review_form(abstract, reviewed_for_tracks[0])
    judgment_form = AbstractJudgmentForm(abstract=abstract, formdata=None)
    review_track_list_form = AbstractReviewedForTracksForm(event=abstract.event, obj=abstract, formdata=None)
    track_session_map = {track.id: track.default_session_id for track in abstract.event.tracks}
    can_manage = abstract.event.can_manage(session.user)
    field_values = filter_field_values(abstract.field_values, can_manage, abstract.user_owns(session.user))
    params = {'abstract': abstract,
              'comment_form': comment_form,
              'review_form': review_form,
              'review_track_list_form': review_track_list_form,
              'judgment_form': judgment_form,
              'visible_tracks': get_visible_reviewed_for_tracks(abstract, session.user),
              'management': management,
              'track_session_map': track_session_map,
              'field_values': field_values}

    if view_class:
        return view_class.render_template('abstract.html', abstract.event, **params)
    else:
        return render_template('events/abstracts/abstract.html', no_javascript=True, standalone=True, **params)

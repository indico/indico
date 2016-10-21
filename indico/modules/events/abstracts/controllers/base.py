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

from flask import render_template, redirect, request, session
from werkzeug.exceptions import Forbidden

from indico.modules.events.abstracts.forms import AbstractJudgmentForm, make_review_form
from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data


def build_review_form(abstract, track):
    review_form_class = make_review_form(abstract.event_new)
    reviews_for_track = abstract.get_reviews(user=session.user, track=track)
    review_for_track = reviews_for_track[0] if reviews_for_track else None

    if review_for_track:
        answers = {'question_{}'.format(rating.question.id): rating.value
                   for rating in review_for_track.ratings}
        defaults = FormDefaults(obj=review_for_track, **answers)
    else:
        defaults = FormDefaults()

    return review_form_class(prefix="track-{}".format(track.id), obj=defaults, abstract=abstract)


def render_abstract_page(abstract, management=False):
    review_forms = {track.id: build_review_form(abstract, track)
                    for track in abstract.reviewed_for_tracks
                    if track.can_review_abstracts(session.user)}
    judgment_form = AbstractJudgmentForm(abstract=abstract)

    return render_template('events/abstracts/abstract.html', abstract=abstract, judgment_form=judgment_form,
                           review_forms=review_forms, management=management, no_javascript=True)


class AbstractMixin:
    normalize_url_spec = {
        'locators': {
            lambda self: self.abstract
        }
    }

    def _checkParams(self):
        self.abstract = Abstract.get_one(request.view_args['abstract_id'], is_deleted=False)

    def _checkProtection(self):
        if not self.abstract.can_access(session.user):
            raise Forbidden


class AbstractPageMixin(AbstractMixin):
    """Display abstract page"""

    def _process(self):
        review_forms = {track.id: build_review_form(self.abstract, track)
                        for track in self.abstract.reviewed_for_tracks
                        if track.can_review_abstracts(session.user)}
        judgment_form = AbstractJudgmentForm(abstract=self.abstract)

        return self.page_class.render_template('abstract.html', self._conf, abstract=self.abstract,
                                               judgment_form=judgment_form, review_forms=review_forms,
                                               management=self.management)


class DisplayAbstractListMixin:
    """Display the list of abstracts"""

    view_class = None
    template = None

    def _process(self):
        if self.list_generator.static_link_used:
            return redirect(self.list_generator.get_list_url())
        return self._render_template(**self.list_generator.get_list_kwargs())

    def _render_template(self, **kwargs):
        return self.view_class.render_template(self.template, self._conf, event=self.event_new, **kwargs)


class CustomizeAbstractListMixin:
    """Filter options and columns to display for the abstract list of an event"""

    view_class = None

    def _process_GET(self):
        list_config = self.list_generator._get_config()
        return self.view_class.render_template('management/abstract_list_filter.html', self._conf,
                                               event=self.event_new, visible_items=list_config['items'],
                                               static_items=self.list_generator.static_items,
                                               extra_filters=self.list_generator.extra_filters,
                                               filters=list_config['filters'])

    def _process_POST(self):
        self.list_generator.store_configuration()
        return jsonify_data(flash=False, **self.list_generator.render_list())

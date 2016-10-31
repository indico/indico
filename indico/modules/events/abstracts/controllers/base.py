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

from flask import render_template, request, session
from werkzeug.exceptions import Forbidden

from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.modules.events.abstracts.forms import AbstractJudgmentForm, make_review_form
from indico.web.forms.base import FormDefaults


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

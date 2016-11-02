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
from flask import flash, request, session, jsonify
from sqlalchemy.orm import joinedload
from werkzeug.exceptions import Forbidden

from indico.modules.events.abstracts.controllers.base import AbstractMixin, build_review_form, render_abstract_page
from indico.modules.events.abstracts.forms import AbstractJudgmentForm
from indico.modules.events.abstracts.models.abstracts import Abstract, AbstractState, AbstractPublicState
from indico.modules.events.abstracts.models.files import AbstractFile
from indico.modules.events.abstracts.models.reviews import AbstractReview
from indico.modules.events.abstracts.models.review_ratings import AbstractReviewRating
from indico.modules.events.abstracts.operations import judge_abstract, reset_abstract_state, withdraw_abstract
from indico.modules.events.tracks.models.tracks import Track
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
from indico.web.util import jsonify_data

from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


class RHAbstractReviewBase(AbstractMixin, RHConferenceBaseDisplay):
    CSRF_ENABLED = True

    def _checkProtection(self):
        RHConferenceBaseDisplay._checkProtection(self)
        AbstractMixin._checkProtection(self)

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        AbstractMixin._checkParams(self)
        self.management = request.view_args.get('management')


class RHAbstractsDownloadAttachment(RHAbstractReviewBase):
    """Download an attachment file belonging to an abstract."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.abstract_file
        }
    }

    def _checkParams(self, params):
        RHAbstractReviewBase._checkParams(self, params)
        self.abstract_file = AbstractFile.get_one(request.view_args['file_id'])

    def _process(self):
        return self.abstract_file.send()


class RHListOtherAbstracts(RHConferenceBaseDisplay):
    """AJAX endpoint that lists all abstracts in the event (dict representation)."""

    CSRF_ENABLED = True

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.excluded_ids = set(request.form.getlist('excluded_abstract_id'))

    def _process(self):
        query = (Abstract
                 .query.with_parent(self.event_new)
                 .options(joinedload('submitter').lazyload('*'))
                 .filter(Abstract.id.notin_(self.excluded_ids))
                 .order_by(Abstract.friendly_id))

        result = [{'id': abstract.id, 'friendly_id': abstract.friendly_id, 'title': abstract.title,
                   'full_title': '#{}: {}'.format(abstract.friendly_id, abstract.title)}
                  for abstract in query
                  if abstract.can_access(session.user)]
        return jsonify(result)


class RHJudgeAbstract(RHAbstractReviewBase):
    def _checkProtection(self):
        if not self.abstract.can_judge(session.user, check_state=True):
            raise Forbidden
        RHAbstractReviewBase._checkProtection(self)

    def _process(self):
        form = AbstractJudgmentForm(abstract=self.abstract)
        if form.validate_on_submit():
            judgment_data, abstract_data = form.split_data
            judge_abstract(self.abstract, abstract_data, judge=session.user, **judgment_data)
            return jsonify_data(page_html=render_abstract_page(self.abstract, management=self.management))

        tpl = get_template_module('events/abstracts/abstract/judge.html')
        return jsonify_data(box_html=tpl.render_decision_box(self.abstract, form, management=self.management))


class RHResetAbstractState(RHAbstractReviewBase):
    def _checkProtection(self):
        if self.abstract.state == AbstractState.submitted:
            raise Forbidden
        # only let pass through
        # - judges (when abstract is not in withdrawn state)
        # - managers (all states except for 'submitted')
        if not self.abstract.can_judge(session.user) or self.abstract.state == AbstractState.withdrawn:
            if not self.event_new.can_manage(session.user):
                raise Forbidden
        RHAbstractReviewBase._checkProtection(self)

    def _process(self):
        if self.abstract.state != AbstractState.submitted:
            reset_abstract_state(self.abstract)
            flash(_("Abstract state has been reset"), 'success')
        html = render_abstract_page(self.abstract, management=self.management)
        return jsonify_data(display_html=html, management_html=html)


class RHWithdrawAbstract(RHAbstractReviewBase):
    def _checkProtection(self):
        if not self.abstract.can_withdraw(session.user, check_state=True):
            raise Forbidden
        RHAbstractReviewBase._checkProtection(self)

    def _process(self):
        if self.abstract.state != AbstractState.withdrawn:
            withdraw_abstract(self.abstract)
            flash(_("Abstract has been withdrawn"), 'success')
        html = render_abstract_page(self.abstract, management=self.management)
        return jsonify_data(display_html=html, management_html=html)


class RHReviewAbstractForTrack(RHAbstractReviewBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.abstract,
            lambda self: self.track
        }
    }

    def _checkProtection(self):
        if not self.abstract.can_review(session.user, check_state=True):
            raise Forbidden
        RHAbstractReviewBase._checkProtection(self)

    def _checkParams(self, params):
        RHAbstractReviewBase._checkParams(self, params)
        self.track = Track.get_one(request.view_args['track_id'])
        reviews = self.abstract.get_reviews(user=session.user, track=self.track)
        self.review = reviews[0] if reviews else None

    def _process(self):
        form = build_review_form(self.abstract, self.track)

        if form.validate_on_submit():
            if self.review:
                form.populate_obj(self.review)
                for question in self.event_new.abstract_review_questions:
                    rating = question.get_review_rating(self.review)
                    if not rating:
                        rating = AbstractReviewRating(question=question, review=self.review)
                    rating.value = int(form.data["question_{}".format(question.id)])
            else:
                self.review = AbstractReview(abstract=self.abstract, track=self.track, user=session.user)
                form.populate_obj(self.review)
                for question in self.event_new.abstract_review_questions:
                    value = int(form.data["question_{}".format(question.id)])
                    self.review.ratings.append(
                        AbstractReviewRating(question=question, value=value))
            return jsonify_data(page_html=render_abstract_page(self.abstract, management=self.management))
        tpl = get_template_module('events/abstracts/abstract/review.html')
        return jsonify_data(box_html=tpl.render_review_box(form, self.abstract, self.track, management=self.management))

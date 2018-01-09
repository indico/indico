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

from flask import flash, jsonify, request, session
from sqlalchemy.orm import joinedload, subqueryload
from werkzeug.exceptions import Forbidden

from indico.modules.events.abstracts.controllers.base import RHAbstractBase, RHAbstractsBase
from indico.modules.events.abstracts.controllers.common import (AbstractsDownloadAttachmentsMixin, AbstractsExportCSV,
                                                                AbstractsExportExcel, AbstractsExportPDFMixin,
                                                                CustomizeAbstractListMixin, DisplayAbstractListMixin)
from indico.modules.events.abstracts.forms import (AbstractCommentForm, AbstractJudgmentForm,
                                                   AbstractReviewedForTracksForm, build_review_form)
from indico.modules.events.abstracts.lists import AbstractListGeneratorDisplay
from indico.modules.events.abstracts.models.abstracts import Abstract, AbstractState
from indico.modules.events.abstracts.models.comments import AbstractComment
from indico.modules.events.abstracts.models.reviews import AbstractReview
from indico.modules.events.abstracts.operations import (create_abstract_comment, create_abstract_review,
                                                        delete_abstract_comment, judge_abstract, reset_abstract_state,
                                                        update_abstract_comment, update_abstract_review,
                                                        update_reviewed_for_tracks, withdraw_abstract)
from indico.modules.events.abstracts.util import get_track_reviewer_abstract_counts, get_user_tracks
from indico.modules.events.abstracts.views import WPDisplayAbstractsReviewing, render_abstract_page
from indico.modules.events.tracks.models.tracks import Track
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
from indico.web.util import jsonify_data, jsonify_template


class RHListOtherAbstracts(RHAbstractsBase):
    """AJAX endpoint that lists all abstracts in the event (dict representation)."""

    ALLOW_LOCKED = True

    def _check_access(self):
        if not session.user:
            raise Forbidden
        RHAbstractsBase._check_access(self)

    def _process_args(self):
        RHAbstractsBase._process_args(self)
        self.excluded_ids = set(request.form.getlist('excluded_abstract_id'))

    def _process(self):
        query = (Abstract.query
                 .with_parent(self.event)
                 .filter(Abstract.state.notin_({AbstractState.duplicate, AbstractState.merged}))
                 .options(joinedload('submitter').lazyload('*'),
                          subqueryload('reviewed_for_tracks'),
                          subqueryload('person_links').joinedload('person').joinedload('user'))
                 .order_by(Abstract.friendly_id))

        if self.excluded_ids:
            query = query.filter(Abstract.id.notin_(self.excluded_ids))

        result = [{'id': abstract.id, 'friendly_id': abstract.friendly_id, 'title': abstract.title,
                   'full_title': '#{}: {}'.format(abstract.friendly_id, abstract.title)}
                  for abstract in query
                  if abstract.can_access(session.user)]
        return jsonify(result)


class RHJudgeAbstract(RHAbstractBase):
    def _check_abstract_protection(self):
        return self.abstract.can_judge(session.user, check_state=True)

    def _process(self):
        form = AbstractJudgmentForm(abstract=self.abstract)
        if form.validate_on_submit():
            judgment_data, abstract_data = form.split_data
            judge_abstract(self.abstract, abstract_data, judge=session.user, **judgment_data)
            return jsonify_data(flash=False, html=render_abstract_page(self.abstract, management=self.management))
        tpl = get_template_module('events/reviews/_common.html')
        return jsonify(html=tpl.render_decision_box(self.abstract, form, session.user))


class RHResetAbstractState(RHAbstractBase):
    def _check_abstract_protection(self):
        if self.abstract.state == AbstractState.submitted:
            return False
        # manages can always reset
        if self.event.can_manage(session.user):
            return True
        # judges can reset if the abstract has not been withdrawn
        return self.abstract.can_judge(session.user) and self.abstract.state != AbstractState.withdrawn

    def _process(self):
        if self.abstract.state != AbstractState.submitted:
            reset_abstract_state(self.abstract)
            flash(_("Abstract judgment has been reset"), 'success')
        return jsonify_data(html=render_abstract_page(self.abstract, management=self.management))


class RHWithdrawAbstract(RHAbstractBase):
    def _check_abstract_protection(self):
        return self.abstract.can_withdraw(session.user, check_state=True)

    def _process(self):
        if self.abstract.state != AbstractState.withdrawn:
            withdraw_abstract(self.abstract)
            flash(_("Abstract has been withdrawn"), 'success')
        return jsonify_data(html=render_abstract_page(self.abstract, management=self.management))


class RHDisplayAbstractListBase(RHAbstractsBase):
    """Base class for all abstract list operations"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.track
        }
    }

    def _process_args(self):
        RHAbstractsBase._process_args(self)
        self.track = Track.get_one(request.view_args['track_id'])
        self.list_generator = AbstractListGeneratorDisplay(event=self.event, track=self.track)

    def _check_access(self):
        if not self.track.can_review_abstracts(session.user) and not self.track.can_convene(session.user):
            raise Forbidden


class RHSubmitAbstractReview(RHAbstractBase):
    """Review an abstract in a specific track"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.abstract,
            lambda self: self.track
        }
    }

    def _check_abstract_protection(self):
        if self.abstract.get_reviews(user=session.user, group=self.track):
            return False
        return self.abstract.can_review(session.user, check_state=True)

    def _process_args(self):
        RHAbstractBase._process_args(self)
        self.track = Track.get_one(request.view_args['track_id'])

    def _process(self):
        form = build_review_form(self.abstract, self.track)
        if form.validate_on_submit():
            create_abstract_review(self.abstract, self.track, session.user, **form.split_data)
            return jsonify_data(flash=False, html=render_abstract_page(self.abstract, management=self.management))
        tpl = get_template_module('events/reviews/forms.html')
        return jsonify(html=tpl.render_review_form(form, proposal=self.abstract, group=self.track))


class RHEditAbstractReview(RHAbstractBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.review
        }
    }

    def _check_abstract_protection(self):
        return self.review.can_edit(session.user, check_state=True)

    def _process_args(self):
        RHAbstractBase._process_args(self)
        self.review = AbstractReview.get_one(request.view_args['review_id'])

    def _process(self):
        form = build_review_form(review=self.review)
        if form.validate_on_submit():
            update_abstract_review(self.review, **form.split_data)
            return jsonify_data(flash=False, html=render_abstract_page(self.abstract, management=self.management))
        tpl = get_template_module('events/reviews/forms.html')
        return jsonify(html=tpl.render_review_form(form, review=self.review))


class RHSubmitAbstractComment(RHAbstractBase):
    def _check_abstract_protection(self):
        return self.abstract.can_comment(session.user)

    def _process(self):
        form = AbstractCommentForm(abstract=self.abstract, user=session.user)
        if form.validate_on_submit():
            create_abstract_comment(self.abstract, form.data)
            return jsonify_data(flash=False, html=render_abstract_page(self.abstract, management=self.management))
        tpl = get_template_module('events/reviews/forms.html')
        return jsonify(html=tpl.render_comment_form(form, proposal=self.abstract))


class RHAbstractCommentBase(RHAbstractBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.comment
        }
    }

    def _process_args(self):
        RHAbstractBase._process_args(self)
        self.comment = AbstractComment.get_one(request.view_args['comment_id'], is_deleted=False)

    def _check_access(self):
        RHAbstractBase._check_access(self)
        if not self.comment.can_edit(session.user):
            raise Forbidden


class RHEditAbstractComment(RHAbstractCommentBase):
    def _process(self):
        form = AbstractCommentForm(obj=self.comment, abstract=self.abstract, user=session.user,
                                   prefix='edit-comment-{}-'.format(self.comment.id))
        if form.validate_on_submit():
            update_abstract_comment(self.comment, form.data)
            return jsonify_data(flash=False, html=render_abstract_page(self.abstract, management=self.management))
        tpl = get_template_module('events/reviews/forms.html')
        return jsonify(html=tpl.render_comment_form(form, proposal=self.abstract, comment=self.comment, edit=True))


class RHDeleteAbstractComment(RHAbstractCommentBase):
    def _process(self):
        delete_abstract_comment(self.comment)
        return jsonify_data(flash=False)


class RHDisplayReviewableTracks(RHAbstractsBase):
    def _check_access(self):
        if not session.user:
            raise Forbidden
        RHAbstractsBase._check_access(self)

    def _process(self):
        track_reviewer_abstract_count = get_track_reviewer_abstract_counts(self.event, session.user)
        return WPDisplayAbstractsReviewing.render_template('display/tracks.html', self.event,
                                                           abstract_count=track_reviewer_abstract_count,
                                                           tracks=get_user_tracks(self.event, session.user))


class RHDisplayReviewableTrackAbstracts(DisplayAbstractListMixin, RHDisplayAbstractListBase):
    view_class = WPDisplayAbstractsReviewing
    template = 'display/abstracts.html'

    def _render_template(self, **kwargs):
        return DisplayAbstractListMixin._render_template(self, track=self.track, **kwargs)


class RHDisplayAbstractListCustomize(CustomizeAbstractListMixin, RHDisplayAbstractListBase):
    view_class = WPDisplayAbstractsReviewing


class RHDisplayAbstractsActionsBase(RHDisplayAbstractListBase):
    """Base class for classes performing actions on abstract"""

    def _process_args(self):
        RHDisplayAbstractListBase._process_args(self)
        ids = map(int, request.form.getlist('abstract_id'))
        self.abstracts = Abstract.query.with_parent(self.track, 'abstracts_reviewed').filter(Abstract.id.in_(ids)).all()


class RHDisplayAbstractsDownloadAttachments(AbstractsDownloadAttachmentsMixin, RHDisplayAbstractsActionsBase):
    pass


class RHDisplayAbstractsExportPDF(AbstractsExportPDFMixin, RHDisplayAbstractsActionsBase):
    pass


class RHDisplayAbstractsExportCSV(AbstractsExportCSV, RHDisplayAbstractsActionsBase):
    pass


class RHDisplayAbstractsExportExcel(AbstractsExportExcel, RHDisplayAbstractsActionsBase):
    pass


class RHEditReviewedForTrackList(RHAbstractBase):
    def _check_abstract_protection(self):
        return self.abstract.can_judge(session.user, check_state=True)

    def _process(self):
        form = AbstractReviewedForTracksForm(event=self.event, obj=self.abstract)
        if form.validate_on_submit():
            update_reviewed_for_tracks(self.abstract, form.reviewed_for_tracks.data)
            return jsonify_data(flash=False, html=render_abstract_page(self.abstract, management=self.management))
        return jsonify_template('events/abstracts/forms/edit_review_tracks.html', form=form)

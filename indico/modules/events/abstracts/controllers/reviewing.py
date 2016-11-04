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

from indico.modules.events.abstracts.controllers.base import (AbstractMixin, DisplayAbstractListMixin,
                                                              AbstractsExportPDFMixin,
                                                              AbstractsDownloadAttachmentsMixin, AbstractsExportCSV,
                                                              AbstractsExportExcel,
                                                              CustomizeAbstractListMixin, build_review_form,
                                                              render_abstract_page)
from indico.modules.events.abstracts.forms import (AbstractCommentForm, AbstractJudgmentForm,
                                                   AbstractReviewedForTracksForm)
from indico.modules.events.abstracts.models.abstracts import Abstract, AbstractState
from indico.modules.events.abstracts.models.comments import AbstractComment
from indico.modules.events.abstracts.models.files import AbstractFile
from indico.modules.events.abstracts.operations import (judge_abstract, reset_abstract_state, withdraw_abstract,
                                                        create_abstract_comment, delete_abstract_comment,
                                                        update_abstract_comment, create_abstract_review,
                                                        update_abstract_review, update_reviewed_for_tracks)
from indico.modules.events.abstracts.util import (AbstractListGeneratorDisplay, get_track_reviewer_abstract_counts,
                                                  get_user_tracks)
from indico.modules.events.abstracts.views import WPDisplayAbstractsReviewing
from indico.modules.events.tracks.models.tracks import Track
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
from indico.web.util import jsonify_data
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


class RHAbstractsBase(RHConferenceBaseDisplay):
    CSRF_ENABLED = True
    EVENT_FEATURE = 'abstracts'


class RHAbstractReviewBase(AbstractMixin, RHAbstractsBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.abstract
        }
    }

    def _checkProtection(self):
        RHAbstractsBase._checkProtection(self)
        AbstractMixin._checkProtection(self)

    def _checkParams(self, params):
        RHAbstractsBase._checkParams(self, params)
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


class RHListOtherAbstracts(RHAbstractsBase):
    """AJAX endpoint that lists all abstracts in the event (dict representation)."""

    CSRF_ENABLED = True

    def _checkParams(self, params):
        RHAbstractsBase._checkParams(self, params)
        self.excluded_ids = set(request.form.getlist('excluded_abstract_id'))

    def _process(self):
        query = (Abstract
                 .query.with_parent(self.event_new)
                 .filter(Abstract.state.notin_({AbstractState.duplicate, AbstractState.merged}))
                 .options(joinedload('submitter').lazyload('*'))
                 .order_by(Abstract.friendly_id))

        if self.excluded_ids:
            query = query.filter(Abstract.id.notin_(self.excluded_ids))

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


class RHDisplayAbstractListBase(RHAbstractsBase):
    """Base class for all abstract list operations"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.track
        }
    }

    def _checkParams(self, params):
        RHAbstractsBase._checkParams(self, params)
        self.track = Track.get_one(request.view_args['track_id'])
        self.list_generator = AbstractListGeneratorDisplay(event=self.event_new, track=self.track)

    def _checkProtection(self):
        if not self.track.can_review_abstracts(session.user) and not self.track.can_convene(session.user):
            raise Forbidden


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
                update_abstract_review(self.review, **form.split_data)
            else:
                create_abstract_review(self.abstract, self.track, session.user, **form.split_data)
            return jsonify_data(page_html=render_abstract_page(self.abstract, management=self.management))
        tpl = get_template_module('events/abstracts/abstract/review.html')
        return jsonify_data(box_html=tpl.render_review_box(form, self.abstract, self.track, management=self.management))


class RHLeaveComment(RHAbstractReviewBase):
    def _process(self):
        form = AbstractCommentForm()
        if form.validate_on_submit():
            create_abstract_comment(self.abstract, form.data)
            return jsonify_data(page_html=render_abstract_page(self.abstract, management=self.management))
        tpl = get_template_module('events/abstracts/abstract/review.html')
        return jsonify_data(form_html=tpl.render_comment_form(form, self.abstract))


class RHAbstractCommentBase(RHAbstractReviewBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.comment
        }
    }

    def _checkParams(self, params):
        RHAbstractReviewBase._checkParams(self, params)
        self.comment = AbstractComment.get_one(request.view_args['comment_id'])

    def _checkProtection(self):
        RHAbstractReviewBase._checkProtection(self)
        if not self.comment.can_edit(session.user):
            raise Forbidden


class RHEditAbstractComment(RHAbstractCommentBase):
    def _process(self):
        form = AbstractCommentForm(obj=self.comment)
        if form.validate_on_submit():
            update_abstract_comment(self.comment, form.data)
            return jsonify_data(page_html=render_abstract_page(self.abstract, management=self.management))
        tpl = get_template_module('events/abstracts/abstract/review.html')
        return jsonify_data(form_html=tpl.render_comment_form(form, self.abstract, comment=self.comment))


class RHDeleteAbstractComment(RHAbstractCommentBase):
    def _process(self):
        delete_abstract_comment(self.comment)
        return jsonify_data()


class RHDisplayReviewableTracks(RHAbstractsBase):
    def _checkProtection(self):
        RHAbstractsBase._checkProtection(self)
        if not session.user:
            raise Forbidden

    def _process(self):
        track_reviewer_abstract_count = get_track_reviewer_abstract_counts(self.event_new, session.user)

        return WPDisplayAbstractsReviewing.render_template('display/tracks.html', self._conf, event=self.event_new,
                                                           abstract_count=track_reviewer_abstract_count,
                                                           tracks=get_user_tracks(self.event_new, session.user))


class RHDisplayReviewableTrackAbstracts(DisplayAbstractListMixin, RHDisplayAbstractListBase):
    view_class = WPDisplayAbstractsReviewing
    template = 'display/abstracts.html'

    def _render_template(self, **kwargs):
        return DisplayAbstractListMixin._render_template(self, track=self.track, **kwargs)


class RHDisplayAbstractListCustomize(CustomizeAbstractListMixin, RHDisplayAbstractListBase):
    view_class = WPDisplayAbstractsReviewing


class RHDisplayAbstractsActionsBase(RHDisplayAbstractListBase):
    """Base class for classes performing actions on abstract"""

    def _checkParams(self, params):
        RHDisplayAbstractListBase._checkParams(self, params)
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


class RHEditReviewedForTrackList(RHAbstractReviewBase):
    def _checkProtection(self):
        RHAbstractReviewBase._checkProtection(self)
        if not self.abstract.can_judge(session.user, check_state=True):
            raise Forbidden

    def _process(self):
        form = AbstractReviewedForTracksForm(event=self.event_new, obj=self.abstract)
        if form.validate_on_submit:
            update_reviewed_for_tracks(self.abstract, form.reviewed_for_tracks.data)
            return jsonify_data(page_html=render_abstract_page(self.abstract, management=self.management))
        tpl = get_template_module('events/abstracts/abstract/review.html')
        return jsonify_data(box_html=tpl.render_reviewed_for_tracks_box(self.abstract, form=form,
                                                                        management=self.management))

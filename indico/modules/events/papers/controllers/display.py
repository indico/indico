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

from flask import request, session, flash
from werkzeug.exceptions import Forbidden, BadRequest

from indico.core.db import db
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.papers.controllers.base import RHPapersBase
from indico.modules.events.papers.controllers.common import PaperJudgmentMixin
from indico.modules.events.papers.forms import PaperSubmissionForm
from indico.modules.events.papers.lists import PaperJudgingAreaListGeneratorDisplay
from indico.modules.events.papers.operations import create_paper_revision, update_reviewing_roles
from indico.modules.events.papers.settings import PaperReviewingRole
from indico.modules.events.papers.views import WPDisplayJudgingArea
from indico.modules.users import User
from indico.util.i18n import _
from indico.web.util import jsonify_form, jsonify_data, jsonify_template


class RHSubmitPaper(RHPapersBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.contribution
        }
    }

    def _checkParams(self, params):
        RHPapersBase._checkParams(self, params)
        self.contribution = Contribution.get_one(request.view_args['contrib_id'], is_deleted=False)

    def _checkProtection(self):
        RHPapersBase._checkProtection(self)
        if not self.contribution.can_manage(session.user, role='submit'):
            raise Forbidden

    def _process(self):
        form = PaperSubmissionForm()
        if form.validate_on_submit():
            create_paper_revision(self.contribution, session.user, form.files.data)
            return jsonify_data(flash=False)
        return jsonify_form(form, form_header_kwargs={'action': request.relative_url})


class RHPaperTimeline(RHPapersBase):
    def _process(self):
        return NotImplementedError


class RHJudgingAreaBase(RHPapersBase):
    def _checkProtection(self):
        if not session.user or session.user not in self.event_new.cfp.judges:
            raise Forbidden
        RHPapersBase._checkProtection(self)


class RHDisplayJudgingArea(RHJudgingAreaBase):
    def _checkParams(self, params):
        RHJudgingAreaBase._checkParams(self, params)
        self.list_generator = PaperJudgingAreaListGeneratorDisplay(event=self.event_new, user=session.user)

    def _process(self):
        return WPDisplayJudgingArea.render_template('display/judging_area.html', self._conf, event=self.event_new,
                                                    **self.list_generator.get_list_kwargs())


class RHDisplayCustomizeJudgingAreaList(RHJudgingAreaBase):
    """Display dialog with filters"""

    def _checkParams(self, params):
        RHJudgingAreaBase._checkParams(self, params)
        self.list_generator = PaperJudgingAreaListGeneratorDisplay(event=self.event_new, user=session.user)

    def _process_GET(self):
        list_config = self.list_generator.list_config
        return WPDisplayJudgingArea.render_template('management/assignment_list_filter.html', self._conf,
                                                    event=self.event_new,
                                                    static_items=self.list_generator.static_items,
                                                    filters=list_config['filters'],
                                                    visible_items=list_config['items'])

    def _process_POST(self):
        self.list_generator.store_configuration()
        return jsonify_data(flash=False, **self.list_generator.render_list())


class RHDisplayPapersActionsBase(RHJudgingAreaBase):
    """Base class for RHs performing actions on selected contributions"""

    def _checkParams(self, params):
        RHJudgingAreaBase._checkParams(self, params)
        ids = map(int, request.form.getlist('contribution_id'))
        self.contributions = Contribution.query.with_parent(self.event_new).filter(Contribution.id.in_(ids)).all()


class RHDisplayBulkPaperJudgment(PaperJudgmentMixin, RHDisplayPapersActionsBase):
    def _checkParams(self, params):
        RHDisplayPapersActionsBase._checkParams(self, params)
        self.list_generator = PaperJudgingAreaListGeneratorDisplay(event=self.event_new, user=session.user)


class RHRJudgingAreaAssigningBase(RHDisplayPapersActionsBase):
    """Base class for assigning/unassigning paper reviewing roles"""

    def _checkParams(self, params):
        RHDisplayPapersActionsBase._checkParams(self, params)
        self.role = PaperReviewingRole[request.args['role']]

    def _render_template(self, person_list, action):
        user_competences = self.event_new.cfp.user_competences
        competences = {'competences_{}'.format(user_id): competences.competences
                       for user_id, competences in user_competences.iteritems()}
        return jsonify_template('events/papers/management/assign_role.html', event=self.event_new, role=self.role.name,
                                action=action, person_list=person_list, competences=competences,
                                contribs=self.contributions)


class RHJudgingAreaAssign(RHRJudgingAreaAssigningBase):
    """"Renders the person list to assign paper reviewing roles"""

    def _process(self):
        if self.role == PaperReviewingRole.content_reviewer:
            person_list = self.event_new.cfp.content_reviewers
        elif self.role == PaperReviewingRole.layout_reviewer:
            person_list = self.event_new.cfp.layout_reviewers
        else:
            raise BadRequest
        return self._render_template(person_list, 'assign')


class RHJudgingAreaUnassign(RHRJudgingAreaAssigningBase):
    """"Renders the person list to unassign paper reviewing roles"""

    def _process(self):
        person_list = set()
        for contribution in self.contributions:
            if self.role == PaperReviewingRole.content_reviewer:
                person_list |= contribution.paper_content_reviewers
            elif self.role == PaperReviewingRole.layout_reviewer:
                person_list |= contribution.paper_layout_reviewers

        return self._render_template(person_list, 'unassign')


class RHAssignRole(RHDisplayPapersActionsBase):
    """Assign/unassign paper reviewing roles"""

    def _checkParams(self, params):
        RHDisplayPapersActionsBase._checkParams(self, params)
        person_ids = request.form.getlist('person_id')
        self.persons = User.query.filter(User.id.in_(person_ids)).all()
        self.action = request.form.get('action')
        self.role = PaperReviewingRole[request.form.get('role')]

    def _process(self):
        update_reviewing_roles(self.event_new, self.persons, self.contributions, self.role, self.action)
        if self.action == 'assign':
            flash(_("Paper reviewing roles have been assigned."), 'success')
        else:
            flash(_("Paper reviewing roles have been unassigned."), 'success')
        return jsonify_data(flash=False)

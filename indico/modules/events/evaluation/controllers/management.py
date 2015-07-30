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

from flask import redirect, request, flash
from werkzeug.exceptions import NotFound

from indico.core.db import db
from indico.modules.events.evaluation.fields import get_field_types
from indico.modules.events.evaluation.forms import EvaluationForm
from indico.modules.events.evaluation.models.evaluations import Evaluation
from indico.modules.events.evaluation.models.questions import EvaluationQuestion
from indico.modules.events.evaluation.views import WPManageEvaluation
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHManageEvaluationsBase(RHConferenceModifBase):
    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.event = self._conf


class RHManageEvaluations(RHManageEvaluationsBase):
    def _process(self):
        evaluations = Evaluation.find_all(event_id=self.event.id)
        return WPManageEvaluation.render_template('management.html', self.event, event=self.event,
                                                  evaluations=evaluations)


class RHManageEvaluation(RHManageEvaluationsBase):
    def _checkParams(self, params):
        RHManageEvaluationsBase._checkParams(self, params)
        self.evaluation = Evaluation.get(request.view_args['evaluation_id'])

    def _process(self):
        return WPManageEvaluation.render_template('manage_evaluation.html', self.event, evaluation=self.evaluation)


class RHEditEvaluation(RHManageEvaluation):
    def _process(self):
        form = EvaluationForm(event=self.event, obj=FormDefaults(self.evaluation))
        if form.validate_on_submit():
            form.populate_obj(self.evaluation)
            flash(_('Evaluation modified'), 'success')
            return redirect(url_for('.manage_evaluation', self.evaluation))
        return WPManageEvaluation.render_template('edit_evaluation.html', self.event,
                                                  evaluation=self.evaluation, form=form)


class RHCreateEvaluation(RHManageEvaluationsBase):
    def _process(self):
        form = EvaluationForm(event=self.event)
        if form.validate_on_submit():
            evaluation = Evaluation(event=self.event)
            form.populate_obj(evaluation)
            db.session.add(evaluation)
            db.session.flush()
            flash(_('Evaluation created'), 'success')
            return redirect(url_for('.manage_evaluation', evaluation))
        return WPManageEvaluation.render_template('create_evaluation.html', self.event, form=form)


class RHManageEvaluationQuestions(RHManageEvaluationsBase):
    def _process(self):
        return 'TODO'


class RHAddEvaluationQuestion(RHManageEvaluationsBase):
    def _process(self):
        try:
            field_cls = get_field_types()[request.view_args['type']]
        except KeyError:
            raise NotFound

        form = field_cls.config_form()
        if form.validate_on_submit():
            question = EvaluationQuestion(event=self.event)
            field_cls(question).save_config(form)
            db.session.add(question)
            db.session.flush()
            flash(_('Question "{title}" added').format(title=question.title), 'success')
            return redirect(url_for('.manage_questions', self.event))
        return WPManageEvaluation.render_template('edit_question.html', self.event, form=form)


class RHEditEvaluationQuestion(RHManageEvaluationsBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.question.event
        },
        'preserved_args': {'question_id'}
    }

    def _checkParams(self, params):
        RHManageEvaluationsBase._checkParams(self, params)
        self.question = EvaluationQuestion.get_one(request.view_args['question_id'])

    def _process(self):
        form = self.question.field.config_form(obj=FormDefaults(self.question, **self.question.field_data))
        if form.validate_on_submit():
            self.question.field.save_config(form)
            db.session.flush()
            flash(_('Question "{title}" updated').format(title=self.question.title), 'success')
            return redirect(url_for('.manage_questions', self.event))
        return WPManageEvaluation.render_template('edit_question.html', self.event, form=form, question=self.question)

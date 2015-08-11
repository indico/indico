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

from flask import redirect, request, flash, jsonify
from werkzeug.exceptions import NotFound

from indico.core.db import db
from indico.modules.events.surveys.fields import get_field_types
from indico.modules.events.surveys.forms import SurveyForm, ScheduleSurveyForm
from indico.modules.events.surveys.models.surveys import Survey, SurveyState
from indico.modules.events.surveys.models.questions import SurveyQuestion
from indico.modules.events.surveys.util import make_survey_form
from indico.modules.events.surveys.views import WPManageSurvey
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_template, jsonify_data
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHManageSurveysBase(RHConferenceModifBase):
    CSRF_ENABLED = True

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.event = self._conf


class RHManageSurveyBase(RHManageSurveysBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.survey
        }
    }

    def _checkParams(self, params):
        RHManageSurveysBase._checkParams(self, params)
        self.survey = Survey.find_one(id=request.view_args['survey_id'], is_deleted=False)


class RHManageSurveys(RHManageSurveysBase):
    def _process(self):
        surveys = Survey.find(event_id=self.event.id).order_by(db.func.lower(Survey.title)).all()
        return WPManageSurvey.render_template('management.html', self.event, event=self.event, surveys=surveys)


class RHManageSurvey(RHManageSurveyBase):
    def _process(self):
        return WPManageSurvey.render_template('manage_survey.html', self.event, survey=self.survey, states=SurveyState)


class RHEditSurvey(RHManageSurveyBase):
    def _process(self):
        form = SurveyForm(event=self.event, obj=FormDefaults(self.survey))
        if form.validate_on_submit():
            form.populate_obj(self.survey)
            flash(_('Survey modified'), 'success')
            return redirect(url_for('.manage_survey', self.survey))

        return WPManageSurvey.render_template('edit_survey.html', self.event, event=self.event, form=form,
                                              survey=self.survey)


class RHCreateSurvey(RHManageSurveysBase):
    def _process(self):
        form = SurveyForm(obj=FormDefaults(require_user=True), event=self.event)
        if form.validate_on_submit():
            survey = Survey(event=self.event)
            form.populate_obj(survey)
            db.session.add(survey)
            db.session.flush()
            flash(_('Survey created'), 'success')
            return redirect(url_for('.manage_survey', survey))

        return WPManageSurvey.render_template('edit_survey.html', self.event, event=self.event, form=form, survey=None)


class RHScheduleSurvey(RHManageSurvey):
    def _get_form_defaults(self):
        return FormDefaults(self.survey)

    def _process(self):
        form = ScheduleSurveyForm(obj=self._get_form_defaults(), survey=self.survey)
        if form.validate_on_submit():
            self.survey.start_dt = form.start_dt.data
            self.survey.end_dt = form.end_dt.data
            # TODO: open/close/schedule
            flash(_('Survey is now open'), 'success')
            return jsonify_data(flash=False)
        return jsonify_template('events/surveys/schedule_survey.html', form=form)


class RHStartSurvey(RHManageSurvey):
    def _process(self):
        self.survey.start()
        return redirect(url_for('.manage_survey', self.survey))


class RHEndSurvey(RHManageSurvey):
    def _process(self):
        self.survey.end()
        return redirect(url_for('.manage_survey', self.survey))


class RHManageSurveyQuestionnaire(RHManageSurvey):
    def _process(self):
        field_types = get_field_types()
        preview_form = make_survey_form(self.survey.questions)()

        return WPManageSurvey.render_template('manage_questionnaire.html', self.event, survey=self.survey,
                                              field_types=field_types, preview_form=preview_form)


class RHAddSurveyQuestion(RHManageSurvey):
    normalize_url_spec = {
        'locators': {
            lambda self: self.survey
        },
        'preserved_args': {'type'}
    }

    def _process(self):
        try:
            field_cls = get_field_types()[request.view_args['type']]
        except KeyError:
            raise NotFound

        form = field_cls.config_form()
        if form.validate_on_submit():
            question = SurveyQuestion(survey_id=self.survey.id)
            field_cls(question).save_config(form)
            db.session.add(question)
            db.session.flush()
            flash(_('Question "{title}" added').format(title=question.title), 'success')
            return jsonify_data(flash=False)
        return jsonify_template('events/surveys/edit_question.html', form=form)


class RHManageSurveyQuestionBase(RHManageSurveysBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.question
        }
    }

    def _checkParams(self, params):
        RHManageSurveysBase._checkParams(self, params)
        self.question = SurveyQuestion.get_one(request.view_args['question_id'])


class RHEditSurveyQuestion(RHManageSurveyQuestionBase):
    def _process(self):
        form = self.question.field.config_form(obj=FormDefaults(self.question, **self.question.field_data))
        if form.validate_on_submit():
            self.question.field.save_config(form)
            db.session.flush()
            flash(_('Question "{title}" updated').format(title=self.question.title), 'success')
            return jsonify_data(flash=False)
        return jsonify_template('events/surveys/edit_question.html', form=form, question=self.question)


class RHDeleteSurveyQuestion(RHManageSurveyQuestionBase):
    def _process(self):
        db.session.delete(self.question)
        db.session.flush()
        flash(_('Question {} successfully deleted'.format(self.question.title)), 'success')
        return redirect(url_for('.manage_questionnaire', self.question.survey))


class RHChangeQuestionPosition(RHManageSurveyBase):
    def _process(self):
        questions = {question.id: question for question in self.survey.questions}
        question_ids = map(int, request.form.getlist('question_ids'))
        for index, question_id in enumerate(question_ids):
            question = questions[question_id]
            question.position = index + 1
        db.session.flush()
        return jsonify(success=True)

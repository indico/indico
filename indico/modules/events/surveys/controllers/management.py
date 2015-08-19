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

from flask import redirect, request, flash, jsonify, session
from werkzeug.exceptions import NotFound

from indico.core.db import db
from indico.modules.events.surveys import logger
from indico.modules.events.surveys.fields import get_field_types
from indico.modules.events.surveys.forms import SurveyForm, ScheduleSurveyForm
from indico.modules.events.surveys.models.surveys import Survey, SurveyState
from indico.modules.events.surveys.models.questions import SurveyQuestion
from indico.modules.events.surveys.util import make_survey_form
from indico.modules.events.surveys.views import WPManageSurvey, WPSurveyResults
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_template, jsonify_data
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHManageSurveysBase(RHConferenceModifBase):
    """Base class for all survey management RHs"""

    CSRF_ENABLED = True

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.event = self._conf


class RHManageSurveyBase(RHManageSurveysBase):
    """Base class for specific survey management RHs."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.survey
        }
    }

    def _checkParams(self, params):
        RHManageSurveysBase._checkParams(self, params)
        self.survey = Survey.find_one(id=request.view_args['survey_id'], is_deleted=False)


class RHManageSurveys(RHManageSurveysBase):
    """Survey management overview (list of surveys)"""

    def _process(self):
        surveys = Survey.find(event_id=self.event.id, is_deleted=False).order_by(db.func.lower(Survey.title)).all()
        return WPManageSurvey.render_template('management.html', self.event, event=self.event, surveys=surveys)


class RHManageSurvey(RHManageSurveyBase):
    """Specific survey management (overview)"""

    def _process(self):
        return WPManageSurvey.render_template('manage_survey.html', self.event, survey=self.survey, states=SurveyState)


class RHSurveyResults(RHManageSurveyBase):
    """Displays summarized results of the survey"""

    def _process(self):
        return WPSurveyResults.render_template('survey_results.html', self.event, survey=self.survey)


class RHEditSurvey(RHManageSurveyBase):
    """Edit a survey's basic data/settings"""

    def _get_form_defaults(self):
        return FormDefaults(self.survey, limit_submissions=self.survey.submission_limit is not None)

    def _process(self):
        form = SurveyForm(event=self.event, obj=self._get_form_defaults())
        if form.validate_on_submit():
            form.populate_obj(self.survey)
            db.session.flush()
            flash(_('Survey modified'), 'success')
            logger.info('Survey {} modified by {}'.format(self.survey, session.user))
            return redirect(url_for('.management', self.event))
        return WPManageSurvey.render_template('edit_survey.html', self.event, event=self.event, form=form,
                                              survey=self.survey)


class RHDeleteSurvey(RHManageSurveyBase):
    """Delete a survey"""

    def _process(self):
        self.survey.is_deleted = True
        flash(_('Survey deleted'), 'success')
        logger.info('Survey {} deleted by {}'.format(self.survey, session.user))
        return redirect(url_for('.management', self.event))


class RHCreateSurvey(RHManageSurveysBase):
    """Create a new survey"""

    def _process(self):
        form = SurveyForm(obj=FormDefaults(require_user=True), event=self.event)
        if form.validate_on_submit():
            survey = Survey(event=self.event)
            form.populate_obj(survey)
            if not form.anonymous.data:
                survey.require_user = True
            db.session.add(survey)
            db.session.flush()
            flash(_('Survey created'), 'success')
            logger.info('Survey {} created by {}'.format(survey, session.user))
            return redirect(url_for('.manage_survey', survey))
        return WPManageSurvey.render_template('edit_survey.html', self.event, event=self.event, form=form, survey=None)


class RHScheduleSurvey(RHManageSurvey):
    """Schedule a survey's start/end dates"""

    def _get_form_defaults(self):
        return FormDefaults(self.survey)

    def _process(self):
        form = ScheduleSurveyForm(obj=self._get_form_defaults(), survey=self.survey)
        allow_reschedule_start = self.survey.state in (SurveyState.ready_to_open, SurveyState.active_and_clean)
        if form.validate_on_submit():
            if allow_reschedule_start:
                self.survey.start_dt = form.start_dt.data
            self.survey.end_dt = form.end_dt.data
            flash(_('Survey was scheduled'), 'success')
            logger.info('Survey {} scheduled by {}'.format(self.survey, session.user))
            return jsonify_data(flash=False)
        disabled_fields = ('start_dt',) if not allow_reschedule_start else ()
        return jsonify_template('events/surveys/schedule_survey.html', form=form, disabled_fields=disabled_fields)


class RHCloseSurvey(RHManageSurvey):
    """Close a survey (prevent users from submitting responses)"""

    def _process(self):
        self.survey.close()
        flash(_("Survey is now closed"), 'success')
        logger.info("Survey {} closed by {}".format(self.survey, session.user))
        return redirect(url_for('.manage_survey', self.survey))


class RHOpenSurvey(RHManageSurvey):
    """Open a survey (allows users to submit responses)"""

    def _process(self):
        if self.survey.state == SurveyState.finished:
            self.survey.end_dt = None
        else:
            self.survey.open()
        self.survey.send_start_notification()
        flash(_("Survey is now open"), 'success')
        logger.info("Survey {} opened by {}".format(self.survey, session.user))
        return redirect(url_for('.manage_survey', self.survey))


class RHManageSurveyQuestionnaire(RHManageSurvey):
    """Manage the questionnaire of a survey (question overview page)"""

    def _process(self):
        field_types = get_field_types()
        preview_form = make_survey_form(self.survey.questions)()

        return WPManageSurvey.render_template('manage_questionnaire.html', self.event, survey=self.survey,
                                              field_types=field_types, preview_form=preview_form)


class RHAddSurveyQuestion(RHManageSurvey):
    """Add a new question to a survey"""

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
            logger.info('Survey question {} added by {}'.format(question, session.user))
            return jsonify_data(questionnaire=_render_questionnaire(self.survey))
        return jsonify_template('events/surveys/edit_question.html', form=form)


class RHManageSurveyQuestionBase(RHManageSurveysBase):
    """Base class for RHs that deal with a specific survey question"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.question
        }
    }

    def _checkParams(self, params):
        RHManageSurveysBase._checkParams(self, params)
        self.question = SurveyQuestion.get_one(request.view_args['question_id'])


class RHEditSurveyQuestion(RHManageSurveyQuestionBase):
    """Edit a survey question"""

    def _process(self):
        form = self.question.field.config_form(obj=FormDefaults(self.question, **self.question.field_data))
        if form.validate_on_submit():
            self.question.field.save_config(form)
            db.session.flush()
            flash(_('Question "{title}" updated').format(title=self.question.title), 'success')
            logger.info('Survey question {} modified by {}'.format(self.question, session.user))
            return jsonify_data(questionnaire=_render_questionnaire(self.question.survey))
        return jsonify_template('events/surveys/edit_question.html', form=form, question=self.question)


class RHDeleteSurveyQuestion(RHManageSurveyQuestionBase):
    """Delete a survey question"""

    def _process(self):
        db.session.delete(self.question)
        db.session.flush()
        flash(_('Question "{title}" deleted'.format(title=self.question.title)), 'success')
        logger.info('Survey question {} deleted by {}'.format(self.question, session.user))
        return jsonify_data(questionnaire=_render_questionnaire(self.question.survey))


class RHSortQuestions(RHManageSurveyBase):
    """Update the order of all survey questions"""

    def _process(self):
        questions = {question.id: question for question in self.survey.questions}
        question_ids = map(int, request.form.getlist('question_ids'))
        for position, question_id in enumerate(question_ids, 1):
            questions[question_id].position = position
        db.session.flush()
        logger.info('Questions in {} reordered by {}'.format(self.survey, session.user))
        return jsonify(success=True)


def _render_questionnaire(survey):
    tpl = get_template_module('events/surveys/_questionnaire.html')
    form = make_survey_form(survey.questions)()
    return tpl.render_questionnaire(survey, form)

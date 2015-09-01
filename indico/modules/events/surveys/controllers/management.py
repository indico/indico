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
from sqlalchemy.orm import defaultload, joinedload
from werkzeug.exceptions import NotFound

from indico.core.db import db
from indico.modules.events.logs.models.entries import EventLogRealm, EventLogKind
from indico.modules.events.surveys import logger
from indico.modules.events.surveys.fields import get_field_types
from indico.modules.events.surveys.forms import SurveyForm, ScheduleSurveyForm, SectionForm, TextForm
from indico.modules.events.surveys.models.submissions import SurveySubmission
from indico.modules.events.surveys.models.surveys import Survey, SurveyState
from indico.modules.events.surveys.models.items import (SurveyQuestion, SurveySection, SurveyText, SurveyItem,
                                                        SurveyItemType)
from indico.modules.events.surveys.util import make_survey_form, generate_csv_from_survey
from indico.modules.events.surveys.views import WPManageSurvey, WPSurveyResults
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for, send_file
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
        return WPManageSurvey.render_template('management/survey_list.html',
                                              self.event, event=self.event, surveys=surveys)


class RHManageSurvey(RHManageSurveyBase):
    """Specific survey management (overview)"""

    def _process(self):
        return WPManageSurvey.render_template('management/survey.html', self.event, survey=self.survey)


class RHSurveyResults(RHManageSurveyBase):
    """Displays summarized results of the survey"""

    def _checkParams(self, params):
        RHManageSurveysBase._checkParams(self, params)
        # include all the sections and children to avoid querying them in a loop
        self.survey = (Survey
                       .find(id=request.view_args['survey_id'], is_deleted=False)
                       .options(joinedload(Survey.sections).joinedload(SurveySection.children))
                       .one())

    def _process(self):
        return WPSurveyResults.render_template('management/survey_results.html', self.event, survey=self.survey)


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
            return redirect(url_for('.manage_survey', self.survey))
        return WPManageSurvey.render_template('management/edit_survey.html', self.event, event=self.event, form=form,
                                              survey=self.survey)


class RHDeleteSurvey(RHManageSurveyBase):
    """Delete a survey"""

    def _process(self):
        self.survey.is_deleted = True
        flash(_('Survey deleted'), 'success')
        logger.info('Survey {} deleted by {}'.format(self.survey, session.user))
        return redirect(url_for('.manage_survey_list', self.event))


class RHCreateSurvey(RHManageSurveysBase):
    """Create a new survey"""

    def _process(self):
        form = SurveyForm(obj=FormDefaults(require_user=True), event=self.event)
        if form.validate_on_submit():
            survey = Survey(event_new=self.event.as_event)
            form.populate_obj(survey)
            db.session.add(survey)
            db.session.flush()
            flash(_('Survey created'), 'success')
            logger.info('Survey {} created by {}'.format(survey, session.user))
            return redirect(url_for('.manage_survey', survey))
        return WPManageSurvey.render_template('management/edit_survey.html',
                                              self.event, event=self.event, form=form, survey=None)


class RHScheduleSurvey(RHManageSurveyBase):
    """Schedule a survey's start/end dates"""

    def _get_form_defaults(self):
        return FormDefaults(self.survey)

    def _process(self):
        allow_reschedule_start = self.survey.state in (SurveyState.ready_to_open, SurveyState.active_and_clean,
                                                       SurveyState.finished)
        form = ScheduleSurveyForm(obj=self._get_form_defaults(), survey=self.survey,
                                  allow_reschedule_start=allow_reschedule_start)
        if form.validate_on_submit():
            if allow_reschedule_start:
                self.survey.start_dt = form.start_dt.data
                if getattr(form, 'resend_start_notification', False):
                    self.survey.start_notification_sent = not form.resend_start_notification.data
            self.survey.end_dt = form.end_dt.data
            flash(_('Survey was scheduled'), 'success')
            logger.info('Survey {} scheduled by {}'.format(self.survey, session.user))
            return jsonify_data(flash=False)
        disabled_fields = ('start_dt',) if not allow_reschedule_start else ()
        return jsonify_template('events/surveys/management/schedule_survey.html',
                                form=form, disabled_fields=disabled_fields)


class RHCloseSurvey(RHManageSurveyBase):
    """Close a survey (prevent users from submitting responses)"""

    def _process(self):
        self.survey.close()
        flash(_("Survey is now closed"), 'success')
        logger.info("Survey {} closed by {}".format(self.survey, session.user))
        return redirect(url_for('.manage_survey', self.survey))


class RHOpenSurvey(RHManageSurveyBase):
    """Open a survey (allows users to submit responses)"""

    def _process(self):
        if self.survey.state == SurveyState.finished:
            self.survey.end_dt = None
            self.survey.start_notification_sent = False
        else:
            self.survey.open()
        self.survey.send_start_notification()
        flash(_("Survey is now open"), 'success')
        logger.info("Survey {} opened by {}".format(self.survey, session.user))
        return redirect(url_for('.manage_survey', self.survey))


class RHManageSurveyQuestionnaire(RHManageSurveyBase):
    """Manage the questionnaire of a survey (question overview page)"""

    def _process(self):
        field_types = get_field_types()
        preview_form = make_survey_form(self.survey)()
        return WPManageSurvey.render_template('management/survey_questionnaire.html', self.event, survey=self.survey,
                                              field_types=field_types, preview_form=preview_form)


class RHManageSurveySectionBase(RHManageSurveysBase):
    """Base class for RHs that deal with a specific survey section"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.section
        },
        'preserved_args': {'type'}
    }

    def _checkParams(self, params):
        RHManageSurveysBase._checkParams(self, params)
        self.section = SurveySection.find_one(SurveySection.id == request.view_args['section_id'], ~Survey.is_deleted,
                                              _join=Survey, _eager=SurveySection.survey)
        self.survey = self.section.survey


class RHAddSurveyText(RHManageSurveySectionBase):
    """Add a new text item to a survey"""

    def _process(self):
        form = TextForm()
        if form.validate_on_submit():
            text = SurveyText()
            form.populate_obj(text)
            self.section.children.append(text)
            db.session.flush()
            flash(_('Text item added'), 'success')
            logger.info('Survey text item {} added by {}'.format(text, session.user))
            return jsonify_data(questionnaire=_render_questionnaire_preview(self.survey))
        return jsonify_template('events/surveys/management/edit_survey_item.html', form=form)


class RHAddSurveyQuestion(RHManageSurveySectionBase):
    """Add a new question to a survey"""

    def _process(self):
        try:
            field_cls = get_field_types()[request.view_args['type']]
        except KeyError:
            raise NotFound

        form = field_cls.config_form()
        if form.validate_on_submit():
            question = SurveyQuestion()
            field_cls(question).save_config(form)
            self.section.children.append(question)
            db.session.flush()
            flash(_('Question "{title}" added').format(title=question.title), 'success')
            logger.info('Survey question {} added by {}'.format(question, session.user))
            return jsonify_data(questionnaire=_render_questionnaire_preview(self.survey))
        return jsonify_template('events/surveys/management/edit_survey_item.html', form=form)


class RHAddSurveySection(RHManageSurveyBase):
    """Add a new section to a survey"""

    def _process(self):
        form = SectionForm()
        if form.validate_on_submit():
            section = SurveySection(survey=self.survey)
            form.populate_obj(section)
            db.session.add(section)
            db.session.flush()
            flash(_('Section "{title}" added').format(title=section.title), 'success')
            logger.info('Survey section {} added by {}'.format(section, session.user))
            return jsonify_data(questionnaire=_render_questionnaire_preview(self.survey))
        return jsonify_template('events/surveys/management/edit_survey_item.html', form=form,
                                disabled_until_change=False)


class RHEditSurveySection(RHManageSurveySectionBase):
    """Edit a survey section"""

    def _process(self):
        form = SectionForm(obj=FormDefaults(self.section))
        if form.validate_on_submit():
            old_title = self.section.title
            form.populate_obj(self.section)
            db.session.flush()
            flash(_('Section "{title}" updated').format(title=old_title), 'success')
            logger.info('Survey section {} modified by {}'.format(self.section, session.user))
            return jsonify_data(questionnaire=_render_questionnaire_preview(self.survey))
        return jsonify_template('events/surveys/management/edit_survey_item.html', form=form)


class RHDeleteSurveySection(RHManageSurveySectionBase):
    """Delete a survey section and all its questions"""

    def _process(self):
        db.session.delete(self.section)
        db.session.flush()
        flash(_('Section "{title}" deleted').format(title=self.section.title), 'success')
        logger.info('Survey section {} deleted by {}'.format(self.section, session.user))
        return jsonify_data(questionnaire=_render_questionnaire_preview(self.survey))


class RHManageSurveyTextBase(RHManageSurveysBase):
    """Base class for RHs that deal with a specific survey text item"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.text
        }
    }

    def _checkParams(self, params):
        RHManageSurveysBase._checkParams(self, params)
        self.text = SurveyText.find_one(SurveyText.id == request.view_args['text_id'], ~Survey.is_deleted,
                                        _join=Survey, _eager=SurveySection.survey)
        self.survey = self.text.survey


class RHEditSurveyText(RHManageSurveyTextBase):
    """Edit a survey text item"""

    def _process(self):
        form = TextForm(obj=FormDefaults(self.text))
        if form.validate_on_submit():
            form.populate_obj(self.text)
            db.session.flush()
            flash(_('Text item updated'), 'success')
            logger.info('Survey text item {} modified by {}'.format(self.text, session.user))
            return jsonify_data(questionnaire=_render_questionnaire_preview(self.survey))
        return jsonify_template('events/surveys/management/edit_survey_item.html', form=form)


class RHDeleteSurveyText(RHManageSurveyTextBase):
    """Delete a survey text item"""

    def _process(self):
        db.session.delete(self.text)
        db.session.flush()
        flash(_('Text item deleted'), 'success')
        logger.info('Survey question {} deleted by {}'.format(self.text, session.user))
        return jsonify_data(questionnaire=_render_questionnaire_preview(self.text.survey))


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
            old_title = self.question.title
            self.question.field.save_config(form)
            db.session.flush()
            flash(_('Question "{title}" updated').format(title=old_title), 'success')
            logger.info('Survey question {} modified by {}'.format(self.question, session.user))
            return jsonify_data(questionnaire=_render_questionnaire_preview(self.question.survey))
        return jsonify_template('events/surveys/management/edit_survey_item.html', form=form)


class RHDeleteSurveyQuestion(RHManageSurveyQuestionBase):
    """Delete a survey question"""

    def _process(self):
        db.session.delete(self.question)
        db.session.flush()
        flash(_('Question "{title}" deleted').format(title=self.question.title), 'success')
        logger.info('Survey question {} deleted by {}'.format(self.question, session.user))
        return jsonify_data(questionnaire=_render_questionnaire_preview(self.question.survey))


class RHSortItems(RHManageSurveyBase):
    """Sort survey items and/or move them between sections"""

    def _sort_sections(self):
        sections = {section.id: section for section in self.survey.sections}
        section_ids = map(int, request.form.getlist('section_ids'))
        for position, section_id in enumerate(section_ids, 1):
            sections[section_id].position = position
        logger.info('Sections in {} reordered by {}'.format(self.survey, session.user))

    def _sort_items(self):
        section = SurveySection.find_one(survey=self.survey, id=request.form['section_id'],
                                         _eager=SurveySection.children)
        section_items = {x.id: x for x in section.children}
        item_ids = map(int, request.form.getlist('item_ids'))
        changed_section = None
        for position, item_id in enumerate(item_ids, 1):
            try:
                section_items[item_id].position = position
            except KeyError:
                # item is not in section, was probably moved
                item = SurveyItem.find_one(SurveyItem.survey == self.survey, SurveyItem.id == item_id,
                                           SurveyItem.type != SurveyItemType.section, _eager=SurveyItem.parent)
                changed_section = item.parent
                item.position = position
                item.parent = section
                logger.info('Item {} moved to section {} by {}'.format(item, section, session.user))
        logger.info('Items in {} reordered by {}'.format(section, session.user))
        if changed_section is not None:
            for position, item in enumerate(changed_section.children, 1):
                item.position = position

    def _process(self):
        mode = request.form['mode']
        if mode == 'sections':
            self._sort_sections()
        elif mode == 'items':
            self._sort_items()
        db.session.flush()
        return jsonify(success=True)


def _render_questionnaire_preview(survey):
    # load the survey once again with all the necessary data
    survey = (Survey
              .find(id=survey.id)
              .options(joinedload(Survey.sections).joinedload(SurveySection.children))
              .one())
    tpl = get_template_module('events/surveys/management/_questionnaire_preview.html')
    form = make_survey_form(survey)()
    return tpl.render_questionnaire_preview(survey, form, get_field_types())


class RHExportSubmissions(RHManageSurveyBase):
    """Export submissions from the survey to a CSV file"""

    CSRF_ENABLED = False

    def _process(self):
        if not self.survey.submissions:
            flash(_('There are no submissions in this survey'))
            return redirect(url_for('.manage_survey', self.survey))

        submission_ids = set(map(int, request.form.getlist('submission_ids')))
        csv_file = generate_csv_from_survey(self.survey, submission_ids)
        return send_file('submissions-{}.csv'.format(self.survey.id), csv_file, 'text/csv')


class RHSurveySubmissionBase(RHManageSurveysBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.submission
        }
    }

    def _checkParams(self, params):
        RHManageSurveysBase._checkParams(self, params)
        survey_strategy = joinedload('survey')
        answers_strategy = defaultload('answers').joinedload('question')
        self.submission = (SurveySubmission
                           .find(id=request.view_args['submission_id'])
                           .options(answers_strategy, survey_strategy)
                           .one())


class RHDeleteSubmissions(RHManageSurveyBase):
    """Remove submissions from the survey"""

    def _process(self):
        submission_ids = set(map(int, request.form.getlist('submission_ids')))
        for submission in self.survey.submissions[:]:
            if submission.id in submission_ids:
                self.survey.submissions.remove(submission)
                logger.info('Submission {} deleted from survey {}'.format(submission, self.survey))
                self.event.log(EventLogRealm.management, EventLogKind.negative, 'Surveys',
                               'Submission removed from survey "{}"'.format(self.survey.title),
                               data={'Submitter': submission.user.full_name if submission.user else 'Anonymous'})
        return jsonify(success=True)


class RHDisplaySubmission(RHSurveySubmissionBase):
    """Display a single submission-page"""

    def _process(self):
        return WPManageSurvey.render_template('management/survey_submission.html',
                                              self.event, submission=self.submission)

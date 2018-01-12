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

from flask import flash, redirect, request, session
from sqlalchemy.orm import joinedload
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import Forbidden, NotFound

from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.auth.util import redirect_to_login
from indico.modules.events.controllers.base import RHDisplayEventBase
from indico.modules.events.models.events import EventType
from indico.modules.events.surveys.models.submissions import SurveyAnswer, SurveySubmission
from indico.modules.events.surveys.models.surveys import Survey, SurveyState
from indico.modules.events.surveys.util import (is_submission_in_progress, make_survey_form, query_active_surveys,
                                                save_submitted_survey_to_session, was_survey_submitted)
from indico.modules.events.surveys.views import WPDisplaySurveyConference, WPDisplaySurveySimpleEvent
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.web.flask.util import url_for


def _can_redirect_to_single_survey(surveys):
    return len(surveys) == 1 and surveys[0].is_active and not was_survey_submitted(surveys[0])


class RHSurveyBaseDisplay(RHDisplayEventBase):
    @property
    def view_class(self):
        return WPDisplaySurveyConference if self.event.type_ == EventType.conference else WPDisplaySurveySimpleEvent


class RHSurveyList(RHSurveyBaseDisplay):
    def _process(self):
        surveys = (query_active_surveys(self.event)
                   .options(joinedload('questions'),
                            joinedload('submissions'))
                   .all())
        if _can_redirect_to_single_survey(surveys):
            return redirect(url_for('.display_survey_form', surveys[0]))

        return self.view_class.render_template('display/survey_list.html', self.event,
                                               surveys=surveys, states=SurveyState,
                                               is_submission_in_progress=is_submission_in_progress,
                                               was_survey_submitted=was_survey_submitted)


class RHSubmitSurveyBase(RHSurveyBaseDisplay):
    normalize_url_spec = {
        'locators': {
            lambda self: self.survey
        }
    }

    def _check_access(self):
        RHSurveyBaseDisplay._check_access(self)
        if self.survey.require_user and not session.user:
            raise Forbidden(response=redirect_to_login(reason=_('You are trying to answer a survey '
                                                                'that requires you to be logged in')))
        if self.survey.private and request.args.get('token') != self.survey.uuid and not self.submission:
            # We don't use forbidden since that would redirect to login - but logging in won't help here
            raise NotFound

    def _process_args(self):
        RHSurveyBaseDisplay._process_args(self)
        self.survey = (Survey.query
                       .filter(Survey.id == request.view_args['survey_id'], Survey.is_visible)
                       .options(joinedload('submissions'),
                                joinedload('sections').joinedload('children'))
                       .one())
        self.submission = (session.user.survey_submissions.filter_by(survey=self.survey, is_submitted=False).first()
                           if session.user else None)
        if not self.survey.is_active:
            flash(_('This survey is not active'), 'error')
            return redirect(url_for('.display_survey_list', self.event))
        elif was_survey_submitted(self.survey):
            flash(_('You have already answered this survey'), 'error')
            return redirect(url_for('.display_survey_list', self.event))


class RHSubmitSurvey(RHSubmitSurveyBase):
    def _process(self):
        form = self._make_form()
        if form.validate_on_submit():
            submission = self._save_answers(form)
            if submission.is_anonymous:
                submission.user = None
            submission.submitted_dt = now_utc()
            submission.is_submitted = True
            submission.pending_answers = {}
            db.session.flush()
            save_submitted_survey_to_session(submission)
            self.survey.send_submission_notification(submission)
            flash(_('The survey has been submitted'), 'success')
            return redirect(url_for('.display_survey_list', self.event))

        surveys = Survey.query.with_parent(self.event).filter(Survey.is_visible).all()
        if not _can_redirect_to_single_survey(surveys):
            back_button_endpoint = '.display_survey_list'
        elif self.event.type_ != EventType.conference:
            back_button_endpoint = 'events.display'
        else:
            back_button_endpoint = None
        return self.view_class.render_template('display/survey_questionnaire.html', self.event,
                                               form=form, survey=self.survey,
                                               back_button_endpoint=back_button_endpoint,
                                               partial_completion=self.survey.partial_completion)

    def _make_form(self):
        survey_form_class = make_survey_form(self.survey)
        if self.submission and request.method == 'GET':
            return survey_form_class(formdata=MultiDict(self.submission.pending_answers))
        else:
            return survey_form_class()

    @no_autoflush
    def _save_answers(self, form):
        survey = self.survey
        if not self.submission:
            self.submission = SurveySubmission(survey=survey, user=session.user)
        self.submission.is_anonymous = survey.anonymous
        for question in survey.questions:
            answer = SurveyAnswer(question=question, data=getattr(form, 'question_{}'.format(question.id)).data)
            self.submission.answers.append(answer)
        return self.submission


class RHSaveSurveyAnswers(RHSubmitSurveyBase):
    def _check_access(self):
        RHSubmitSurveyBase._check_access(self)
        if not self.survey.partial_completion:
            raise Forbidden

    def _process(self):
        pending_answers = {k: v for k, v in request.form.iterlists() if k.startswith('question_')}
        if not self.submission:
            self.submission = SurveySubmission(survey=self.survey, user=session.user)
        self.submission.pending_answers = pending_answers
        self.submission.is_anonymous = self.survey.anonymous

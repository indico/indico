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

from flask import redirect, flash, session, request
from werkzeug.exceptions import Forbidden

from indico.core.db import db
from indico.modules.auth.util import redirect_to_login
from indico.modules.events.surveys.fields.simple import StaticTextField
from indico.modules.events.surveys.models.submissions import SurveyAnswer, SurveySubmission
from indico.modules.events.surveys.models.surveys import Survey, SurveyState
from indico.modules.events.surveys.util import make_survey_form, was_survey_submitted, save_submitted_survey_to_session
from indico.modules.events.surveys.views import WPDisplaySurvey
from indico.util.i18n import _
from indico.web.flask.util import url_for

from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


class RHSurveyBaseDisplay(RHConferenceBaseDisplay):
    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.event = self._conf


class RHShowSurveyMainInformation(RHSurveyBaseDisplay):
    def _can_redirect_to_survey_form(self, survey):
        return survey.is_active and not was_survey_submitted(survey)

    def _process(self):
        surveys = Survey.find_all(event_id=self.event.getId(), is_deleted=False)
        if len(surveys) == 1 and self._can_redirect_to_survey_form(surveys[0]):
            return redirect(url_for('.display_survey_form', surveys[0]))

        return WPDisplaySurvey.render_template('surveys_list.html', self.event, surveys=surveys,
                                               states=SurveyState, was_survey_submitted=was_survey_submitted)


class RHSubmitSurveyForm(RHSurveyBaseDisplay):
    CSRF_ENABLED = True

    normalize_url_spec = {
        'locators': {
            lambda self: self.survey
        }
    }

    def _checkProtection(self):
        RHSurveyBaseDisplay._checkProtection(self)
        if self.survey.require_user and not session.user:
            raise Forbidden(response=redirect_to_login(reason=_('You are trying to answer a survey '
                                                                'that requires you to be logged in')))

    def _checkParams(self, params):
        RHSurveyBaseDisplay._checkParams(self, params)
        self.survey = Survey.find_one(id=request.view_args['survey_id'], is_deleted=False)

        if not self.survey.is_active or was_survey_submitted(self.survey):
            flash(_('You have already answered this survey'))
            return redirect(url_for('.display_survey_list', self.event))

    def _process(self):
        form = make_survey_form(self.survey.questions)()
        if form.validate_on_submit():
            self._save_answers(form)
            save_submitted_survey_to_session(self.survey)
            flash(_('Your answers has been saved'), 'success')
            return redirect(url_for('.display_survey_list', self.event))

        return WPDisplaySurvey.render_template('survey_submission.html', self.event, form=form,
                                               event=self.event, survey=self.survey)

    def _save_answers(self, form):
        survey = self.survey
        submission = SurveySubmission(survey_id=survey.id)
        if not survey.anonymous:
            submission.user = session.user
        else:
            submission.is_anonymous = True

        db.session.add(submission)
        db.session.flush()

        for question in survey.questions:
            if isinstance(question.field, StaticTextField):
                continue

            answer = SurveyAnswer(
                submission=submission,
                question=question,
                data=getattr(form, 'question_{}'.format(question.id)).data
            )

            db.session.add(answer)
        db.session.flush()

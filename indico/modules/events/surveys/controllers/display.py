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
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.web.flask.util import url_for

from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


def _get_active_surveys(event):
    query = Survey.find(Survey.event_id == int(event.id),
                        Survey.start_dt != None,  # noqa
                        Survey.start_dt <= now_utc(),
                        ~Survey.is_deleted)
    return [s for s in query if s.is_active]


def _can_redirect_to_single_survey(surveys):
    return len(surveys) == 1 and surveys[0].is_active and not was_survey_submitted(surveys[0])


class RHSurveyBaseDisplay(RHConferenceBaseDisplay):
    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.event = self._conf


class RHShowSurveyMainInformation(RHSurveyBaseDisplay):
    def _process(self):
        surveys = _get_active_surveys(self.event)
        if _can_redirect_to_single_survey(surveys):
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

        if not self.survey.is_active:
            flash(_('This survey is not active'), 'error')
            return redirect(url_for('.display_survey_list', self.event))
        elif was_survey_submitted(self.survey):
            flash(_('You have already answered this survey'), 'error')
            return redirect(url_for('.display_survey_list', self.event))

    def _process(self):
        form = make_survey_form(self.survey.questions)()
        if form.validate_on_submit():
            submission = self._save_answers(form)
            save_submitted_survey_to_session(submission)
            flash(_('Your answers has been saved'), 'success')
            return redirect(url_for('.display_survey_list', self.event))

        show_back_button = not _can_redirect_to_single_survey(_get_active_surveys(self.event))
        return WPDisplaySurvey.render_template('survey_submission.html', self.event, form=form,
                                               event=self.event, survey=self.survey, show_back_button=show_back_button)

    def _save_answers(self, form):
        survey = self.survey
        submission = SurveySubmission(survey=survey)
        if survey.anonymous:
            submission.is_anonymous = True
        else:
            submission.user = session.user

        for question in survey.questions:
            if isinstance(question.field, StaticTextField):
                continue
            answer = SurveyAnswer(question=question, data=getattr(form, 'question_{}'.format(question.id)).data)
            submission.answers.append(answer)

        db.session.flush()
        return submission

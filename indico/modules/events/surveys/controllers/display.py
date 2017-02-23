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

from flask import redirect, flash, session, request
from sqlalchemy.orm import joinedload
from werkzeug.exceptions import Forbidden

from indico.core.db import db
from indico.modules.auth.util import redirect_to_login
from indico.modules.events.models.events import EventType
from indico.modules.events.surveys.models.submissions import SurveyAnswer, SurveySubmission
from indico.modules.events.surveys.models.surveys import Survey, SurveyState
from indico.modules.events.surveys.util import make_survey_form, was_survey_submitted, save_submitted_survey_to_session
from indico.modules.events.surveys.views import (WPDisplaySurveyConference, WPDisplaySurveyMeeting,
                                                 WPDisplaySurveyLecture)
from indico.util.i18n import _
from indico.web.flask.util import url_for

from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


def _can_redirect_to_single_survey(surveys):
    return len(surveys) == 1 and surveys[0].is_active and not was_survey_submitted(surveys[0])


class RHSurveyBaseDisplay(RHConferenceBaseDisplay):
    @property
    def view_class(self):
        mapping = {EventType.conference: WPDisplaySurveyConference,
                   EventType.meeting: WPDisplaySurveyMeeting,
                   EventType.lecture: WPDisplaySurveyLecture}
        return mapping[self.event_new.type_]


class RHSurveyList(RHSurveyBaseDisplay):
    def _process(self):
        surveys = (Survey.query.with_parent(self.event_new)
                   .filter(Survey.is_visible)
                   .options(joinedload('questions'),
                            joinedload('submissions'))
                   .all())
        if _can_redirect_to_single_survey(surveys):
            return redirect(url_for('.display_survey_form', surveys[0]))

        return self.view_class.render_template('display/survey_list.html', self._conf, surveys=surveys,
                                               event=self.event_new, states=SurveyState,
                                               was_survey_submitted=was_survey_submitted)


class RHSubmitSurvey(RHSurveyBaseDisplay):
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
        self.survey = (Survey.query
                       .filter(Survey.id == request.view_args['survey_id'], Survey.is_visible)
                       .options(joinedload('submissions'),
                                joinedload('sections').joinedload('children'))
                       .one())

        if not self.survey.is_active:
            flash(_('This survey is not active'), 'error')
            return redirect(url_for('.display_survey_list', self.event_new))
        elif was_survey_submitted(self.survey):
            flash(_('You have already answered this survey'), 'error')
            return redirect(url_for('.display_survey_list', self.event_new))

    def _process(self):
        form = make_survey_form(self.survey)()
        if form.validate_on_submit():
            submission = self._save_answers(form)
            save_submitted_survey_to_session(submission)
            self.survey.send_submission_notification(submission)
            flash(_('Your answers has been saved'), 'success')
            return redirect(url_for('.display_survey_list', self.event_new))

        surveys = Survey.query.with_parent(self.event_new).filter(Survey.is_visible).all()
        if not _can_redirect_to_single_survey(surveys):
            back_button_endpoint = '.display_survey_list'
        elif self.event_new.type_ != EventType.conference:
            back_button_endpoint = 'events.display'
        else:
            back_button_endpoint = None
        return self.view_class.render_template('display/survey_questionnaire.html', self._conf, form=form,
                                               event=self.event_new, survey=self.survey,
                                               back_button_endpoint=back_button_endpoint)

    def _save_answers(self, form):
        survey = self.survey
        submission = SurveySubmission(survey=survey)
        if not survey.anonymous:
            submission.user = session.user
        for question in survey.questions:
            answer = SurveyAnswer(question=question, data=getattr(form, 'question_{}'.format(question.id)).data)
            submission.answers.append(answer)
        db.session.flush()
        return submission

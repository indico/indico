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

from flask import flash, session, redirect

from indico.core.db import db
from indico.modules.events.surveys import logger
from indico.modules.events.surveys.controllers.management import RHManageSurveysBase, RHManageSurveyBase
from indico.modules.events.surveys.forms import SurveyForm, ScheduleSurveyForm
from indico.modules.events.surveys.models.items import SurveySection
from indico.modules.events.surveys.models.surveys import Survey, SurveyState
from indico.modules.events.surveys.views import WPManageSurvey
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_template


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
            # add a default section so people can start adding questions right away
            survey.items.append(SurveySection(display_as_section=False))
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

# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import flash, redirect, session

from indico.core.db import db
from indico.core.notifications import make_email, send_email
from indico.modules.events.surveys import logger
from indico.modules.events.surveys.controllers.management import RHManageSurveyBase, RHManageSurveysBase
from indico.modules.events.surveys.forms import InvitationForm, ScheduleSurveyForm, SurveyForm
from indico.modules.events.surveys.models.items import SurveySection
from indico.modules.events.surveys.models.surveys import Survey, SurveyState
from indico.modules.events.surveys.views import WPManageSurvey
from indico.util.i18n import _, ngettext
from indico.util.placeholders import replace_placeholders
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


class RHManageSurveys(RHManageSurveysBase):
    """Survey management overview (list of surveys)."""

    def _process(self):
        surveys = (Survey.query.with_parent(self.event)
                   .filter(~Survey.is_deleted)
                   .order_by(db.func.lower(Survey.title))
                   .all())
        return WPManageSurvey.render_template('management/survey_list.html', self.event, surveys=surveys)


class RHManageSurvey(RHManageSurveyBase):
    """Specific survey management (overview)."""

    def _process(self):
        submitted_surveys = [s for s in self.survey.submissions if s.is_submitted]
        return WPManageSurvey.render_template('management/survey.html', self.event,
                                              survey=self.survey, submitted_surveys=submitted_surveys)


class RHEditSurvey(RHManageSurveyBase):
    """Edit a survey's basic data/settings."""

    def _get_form_defaults(self):
        return FormDefaults(self.survey, limit_submissions=self.survey.submission_limit is not None)

    def _process(self):
        form = SurveyForm(event=self.event, obj=self._get_form_defaults())
        if form.validate_on_submit():
            form.populate_obj(self.survey)
            db.session.flush()
            flash(_('Survey modified'), 'success')
            logger.info('Survey %s modified by %s', self.survey, session.user)
            return jsonify_data(flash=False)
        return jsonify_template('events/surveys/management/edit_survey.html', event=self.event, form=form,
                                survey=self.survey)


class RHDeleteSurvey(RHManageSurveyBase):
    """Delete a survey."""

    def _process(self):
        self.survey.is_deleted = True
        flash(_('Survey deleted'), 'success')
        logger.info('Survey %s deleted by %s', self.survey, session.user)
        return redirect(url_for('.manage_survey_list', self.event))


class RHCreateSurvey(RHManageSurveysBase):
    """Create a new survey."""

    def _process(self):
        form = SurveyForm(obj=FormDefaults(require_user=True), event=self.event)
        if form.validate_on_submit():
            survey = Survey(event=self.event)
            # add a default section so people can start adding questions right away
            survey.items.append(SurveySection(display_as_section=False))
            form.populate_obj(survey)
            db.session.add(survey)
            db.session.flush()
            flash(_('Survey created'), 'success')
            logger.info('Survey %s created by %s', survey, session.user)
            return jsonify_data(flash=False)
        return jsonify_template('events/surveys/management/edit_survey.html', event=self.event, form=form,
                                survey=None)


class RHScheduleSurvey(RHManageSurveyBase):
    """Schedule a survey's start/end dates."""

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
            logger.info('Survey %s scheduled by %s', self.survey, session.user)
            return jsonify_data(flash=False)
        disabled_fields = ('start_dt',) if not allow_reschedule_start else ()
        return jsonify_form(form, submit=_('Schedule'), disabled_fields=disabled_fields)


class RHCloseSurvey(RHManageSurveyBase):
    """Close a survey (prevent users from submitting responses)."""

    def _process(self):
        self.survey.close()
        flash(_("Survey is now closed"), 'success')
        logger.info("Survey %s closed by %s", self.survey, session.user)
        return redirect(url_for('.manage_survey', self.survey))


class RHOpenSurvey(RHManageSurveyBase):
    """Open a survey (allows users to submit responses)."""

    def _process(self):
        if self.survey.state == SurveyState.finished:
            self.survey.end_dt = None
            self.survey.start_notification_sent = False
        else:
            self.survey.open()
        self.survey.send_start_notification()
        flash(_("Survey is now open"), 'success')
        logger.info("Survey %s opened by %s", self.survey, session.user)
        return redirect(url_for('.manage_survey', self.survey))


class RHSendSurveyLinks(RHManageSurveyBase):
    """Send emails with URL of the survey."""

    def _process(self):
        tpl = get_template_module('events/surveys/emails/survey_link_email.html', event=self.event)
        form = InvitationForm(body=tpl.get_html_body(), subject=tpl.get_subject(), event=self.event)
        if form.validate_on_submit():
            self._send_emails(form, form.recipients.data)
            num = len(form.recipients.data)
            flash(ngettext('Your email has been sent.', '{} emails have been sent.', num).format(num))
            return jsonify_data(flash=True)
        return jsonify_form(form)

    def _send_emails(self, form, recipients):
        for recipient in recipients:
            email_body = replace_placeholders('survey-link-email', form.body.data, event=self.event,
                                              survey=self.survey)
            email_subject = replace_placeholders('survey-link-email', form.subject.data, event=self.event,
                                                 survey=self.survey)
            tpl = get_template_module('emails/custom.html', subject=email_subject, body=email_body)
            bcc = [session.user.email] if form.copy_for_sender.data else []
            email = make_email(to_list=recipient, bcc_list=bcc, from_address=form.from_address.data,
                               template=tpl, html=True)
            send_email(email, self.event, 'Surveys')

# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import flash, jsonify, redirect, session
from marshmallow import fields
from webargs import validate
from webargs.flaskparser import abort

from indico.core.db import db
from indico.core.notifications import make_email, send_email
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.events.surveys import logger
from indico.modules.events.surveys.controllers.management import RHManageSurveyBase, RHManageSurveysBase
from indico.modules.events.surveys.forms import ScheduleSurveyForm, SurveyForm
from indico.modules.events.surveys.models.items import SurveySection
from indico.modules.events.surveys.models.surveys import Survey, SurveyState
from indico.modules.events.surveys.views import WPManageSurvey
from indico.util.i18n import _
from indico.util.marshmallow import LowercaseString, make_validate_indico_placeholders, no_relative_urls, not_empty
from indico.util.placeholders import get_sorted_placeholders, replace_placeholders
from indico.web.args import use_kwargs
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
        flash(_('Survey is now closed'), 'success')
        logger.info('Survey %s closed by %s', self.survey, session.user)
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
        flash(_('Survey is now open'), 'success')
        logger.info('Survey %s opened by %s', self.survey, session.user)
        return redirect(url_for('.manage_survey', self.survey))


class RHAPIEmailEventSurveyMetadata(RHManageSurveyBase):
    def _process(self):
        with self.event.force_event_locale():
            tpl = get_template_module('events/surveys/emails/survey_link_email.html', event=self.event)
            body = tpl.get_html_body()
            subject = tpl.get_subject()
        placeholders = get_sorted_placeholders('survey-link-email')
        return jsonify({
            'senders': list(self.event.get_allowed_sender_emails().items()),
            'body': body,
            'subject': subject,
            'placeholders': [p.serialize() for p in placeholders],
        })


class RHEmailEventSurveyPreview(RHManageSurveyBase):
    """Preview an email with EventSurvey associated placeholders."""

    @use_kwargs({
        'body': fields.String(required=True),
        'subject': fields.String(required=True),
    })
    def _process(self, body, subject):
        email_body = replace_placeholders('survey-link-email', body, event=self.event, survey=self.survey)
        email_subject = replace_placeholders('survey-link-email', subject, event=self.event, survey=self.survey)
        tpl = get_template_module('events/persons/emails/custom_email.html', email_subject=email_subject,
                                  email_body=email_body)
        return jsonify(subject=tpl.get_subject(), body=tpl.get_html_body())


class RHAPIEmailEventSurveySend(RHManageSurveyBase):
    @use_kwargs({
        'from_address': fields.String(required=True, validate=not_empty),
        'body': fields.String(required=True, validate=[
            not_empty,
            no_relative_urls,
            make_validate_indico_placeholders('survey-link-email'),
        ]),
        'subject': fields.String(required=True, validate=not_empty),
        'bcc_addresses': fields.List(LowercaseString(validate=validate.Email())),
        'copy_for_sender': fields.Bool(load_default=False),
        'email_all_participants': fields.Bool(load_default=False),
        'recipients_addresses': fields.List(LowercaseString(validate=validate.Email())),
    })
    def _process(self, from_address, body, subject, bcc_addresses, copy_for_sender,
                 email_all_participants, recipients_addresses):
        if from_address not in self.event.get_allowed_sender_emails():
            abort(422, messages={'from_address': ['Invalid sender address']})
        self.recipients = set()
        if email_all_participants:
            registrations = Registration.get_all_for_event(self.event)
            self.recipients |= {r.email for r in registrations}
        if recipients_addresses:
            self.recipients |= set(recipients_addresses)
        for recipient in self.recipients:
            email_body = replace_placeholders('survey-link-email', body, event=self.event, survey=self.survey)
            email_subject = replace_placeholders('survey-link-email', subject, event=self.event, survey=self.survey)
            bcc = {session.user.email} if copy_for_sender else set()
            bcc.update(bcc_addresses)
            with self.event.force_event_locale():
                tpl = get_template_module('emails/custom.html', subject=email_subject, body=email_body)
                email = make_email(to_list=recipient, bcc_list=bcc, from_address=from_address,
                                   template=tpl, html=True)
            send_email(email, self.event, 'Surveys')
        return jsonify(count=len(self.recipients))

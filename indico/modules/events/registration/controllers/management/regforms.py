# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import timedelta
from operator import itemgetter

from flask import flash, jsonify, redirect, render_template, session
from marshmallow import validate
from webargs import fields
from wtforms.validators import ValidationError

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.features.util import set_feature_enabled
from indico.modules.events.models.events import EventType
from indico.modules.events.payment import payment_settings
from indico.modules.events.registration import logger, registration_settings
from indico.modules.events.registration.controllers.display import ParticipantListMixin
from indico.modules.events.registration.controllers.management import (RHEventManageRegFormBase,
                                                                       RHEventManageRegFormsBase)
from indico.modules.events.registration.forms import (ParticipantsDisplayForm, ParticipantsDisplayFormColumnsForm,
                                                      RegistrationFormScheduleForm, RegistrationManagersForm)
from indico.modules.events.registration.models.registrations import PublishRegistrationsMode, RegistrationData
from indico.modules.events.registration.stats import AccommodationStats, OverviewStats
from indico.modules.events.registration.util import close_registration, create_personal_data_fields
from indico.modules.events.registration.views import (WPEventManageRegistrationForm, WPManageParticipants,
                                                      WPManageRegistration, WPManageRegistrationStats)
from indico.modules.events.util import update_object_principals
from indico.modules.logs.models.entries import EventLogRealm, LogKind
from indico.modules.registration_form.clone import RegistrationFormCloner
from indico.modules.registration_form.controllers.management.regforms import (ManageRegistrationFormsAreaMixin,
                                                                              ManageRegistrationFormsMixin,
                                                                              RegistrationFormCreateMixin,
                                                                              RegistrationFormDeleteMixin,
                                                                              RegistrationFormEditMixin,
                                                                              RegistrationFormModifyMixin)
from indico.modules.registration_form.forms import RegistrationFormCreateForm, RegistrationFormCreateFromTemplateForm
from indico.modules.registration_form.models.forms import Registration, RegistrationForm, RegistrationState
from indico.modules.registration_form.models.items import PersonalDataType, RegistrationFormItemType
from indico.util.date_time import format_human_timedelta, now_utc
from indico.util.i18n import _, force_locale, orig_string
from indico.web.args import use_kwargs
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


class RHEventManageRegistrationForms(ManageRegistrationFormsMixin, RHEventManageRegFormsBase):
    """List all registrations forms for an event."""


class RHEventRegistrationFormCreate(RegistrationFormCreateMixin, RHEventManageRegFormsBase):
    """Create a new registration form for an event."""


class RHParticipantListPreview(ParticipantListMixin, RHEventManageRegFormsBase):
    """Preview the participant list like a registered participant would see it."""

    view_class = WPManageRegistration

    @use_kwargs({'guest': fields.Bool(load_default=False)}, location='query')
    def _process_args(self, guest):
        RHEventManageRegFormsBase._process_args(self)
        self.preview = 'guest' if guest else 'participant'

    def is_participant(self, user):
        return self.preview == 'participant'


class RHEventRegistrationFormManage(ManageRegistrationFormsAreaMixin, RHEventManageRegFormBase):
    """Specific event registration form management."""

    def _process(self):
        return WPEventManageRegistrationForm.render_template('management/regform.html', self.event, regform=self.regform)


class RHManageRegistrationFormsDisplay(RHEventManageRegFormsBase):
    """Customize the display of registrations on the public page."""

    def _process(self):
        regforms = sorted(self.event.registration_forms, key=lambda f: f.title.lower())
        form = ParticipantsDisplayForm(regforms=regforms)
        if form.validate_on_submit():
            data = form.json.data
            registration_settings.set(self.event, 'merge_registration_forms', data['merge_forms'])
            registration_settings.set_participant_list_form_ids(self.event, data['participant_list_forms'])
            registration_settings.set_participant_list_columns(self.event, data['participant_list_columns'])
            flash(_('The participants display settings have been saved.'), 'success')
            return redirect(url_for('.manage_regforms_display', self.event))
        elif form.is_submitted():
            for error in form.error_list:
                flash(error, 'error')

        available_columns = {field[0].name: field[1]['title'] for field in PersonalDataType.FIELD_DATA}
        enabled_columns = []
        disabled_columns = []
        for column_name in registration_settings.get_participant_list_columns(self.event):
            if column_name in available_columns:
                enabled_columns.append({'id': column_name, 'title': available_columns[column_name]})
                del available_columns[column_name]
        for column_name, column_title in available_columns.items():
            disabled_columns.append({'id': column_name, 'title': column_title})
        disabled_columns.sort(key=itemgetter('title'))

        available_forms = {regform.id: regform for regform in regforms}
        sorted_forms = []
        # Handle forms that have already been sorted by the user.
        for form_id in registration_settings.get_participant_list_form_ids(self.event):
            try:
                regform = available_forms[form_id]
            except KeyError:
                continue
            sorted_forms.append(regform)
            del available_forms[form_id]
        sorted_forms.extend(available_forms.values())

        merge_forms = registration_settings.get(self.event, 'merge_registration_forms')
        return WPManageRegistration.render_template('management/regform_display.html', self.event,
                                                    regforms=regforms, enabled_columns=enabled_columns,
                                                    disabled_columns=disabled_columns, sorted_forms=sorted_forms,
                                                    merge_forms=merge_forms, form=form)


class RHManageRegistrationFormDisplay(RHEventManageRegFormBase):
    """
    Choose the columns to be shown on the participant list for
    a particular form.
    """

    def _process(self):
        form = ParticipantsDisplayFormColumnsForm()
        if form.validate_on_submit():
            registration_settings.set_participant_list_columns(self.event, form.json.data['columns'], self.regform)
            flash(_('The settings for "{}" have been saved.').format(self.regform.title), 'success')
            return jsonify_data()

        active_fields = {field.id: field for field in self.regform.active_fields}
        enabled_fields = []
        for field_id in registration_settings.get_participant_list_columns(self.event, self.regform):
            try:
                field = active_fields[field_id]
            except KeyError:
                continue
            enabled_fields.append(field)
            del active_fields[field_id]

        disabled_fields = list(active_fields.values())
        return jsonify_template('registration/management/regform_display_form_columns.html', form=form,
                                enabled_columns=enabled_fields, disabled_columns=disabled_fields)


def _get_regform_creation_log_data(regform):
    with force_locale(None, default=False):
        return {
            'Visibility to participants': orig_string(regform.publish_registrations_participants.title),
            'Visibility to everyone': orig_string(regform.publish_registrations_public.title),
            'Visibility duration': (format_human_timedelta(regform.publish_registrations_duration)
                                    if regform.publish_registrations_duration else 'Indefinite'),
            'Retention period': (format_human_timedelta(regform.retention_period)
                                 if regform.retention_period else 'Indefinite'),
        }


class RHManageParticipants(RHEventManageRegFormsBase):
    """Show and enable the dummy registration form for participants."""

    def _process(self):
        regform = self.event.participation_regform
        registration_enabled = self.event.has_feature('registration')
        participant_visibility = (PublishRegistrationsMode.show_with_consent
                                  if self.event.type_ == EventType.lecture
                                  else PublishRegistrationsMode.show_all)
        public_visibility = (PublishRegistrationsMode.show_with_consent
                             if self.event.type_ == EventType.lecture
                             else PublishRegistrationsMode.show_all)
        form = RegistrationFormCreateForm(title='Participants',
                                          visibility=[participant_visibility.name, public_visibility.name, None])
        if form.validate_on_submit():
            set_feature_enabled(self.event, 'registration', True)
            if not regform:
                regform = RegistrationForm(event=self.event, is_participation=True,
                                           currency=payment_settings.get('currency'))
                create_personal_data_fields(regform)
                form.populate_obj(regform, skip=['visibility'])
                participant_visibility, public_visibility, visibility_duration = form.visibility.data
                regform.publish_registrations_participants = PublishRegistrationsMode[participant_visibility]
                regform.publish_registrations_public = PublishRegistrationsMode[public_visibility]
                regform.publish_registrations_duration = (timedelta(weeks=visibility_duration)
                                                          if visibility_duration is not None else None)
                db.session.add(regform)
                db.session.flush()
                signals.event.registration_form_created.send(regform)
                regform.log(EventLogRealm.management, LogKind.positive, 'Registration',
                            f'Registration form "{regform.title}" has been created', session.user,
                            data=_get_regform_creation_log_data(regform))
            return redirect(url_for('event_registration.manage_regform', regform))

        if not regform or not registration_enabled:
            return WPManageParticipants.render_template('management/participants.html', self.event, form=form,
                                                        regform=regform, registration_enabled=registration_enabled)
        return redirect(url_for('event_registration.manage_regform', regform))


class RHEventRegistrationFormEdit(RegistrationFormEditMixin, RHEventManageRegFormBase):
    """Edit a registration form in an event."""


class RHRegistrationFormNotificationPreview(RHEventManageRegFormBase):
    """Preview registration emails."""

    @use_kwargs({
        'message': fields.String(load_default=''),
        'state': fields.Enum(RegistrationState, required=True, validate=validate.OneOf(
            [RegistrationState.pending, RegistrationState.unpaid, RegistrationState.complete]))
    })
    @no_autoflush
    def _process(self, message, state):
        self.commit = False
        match state:
            case RegistrationState.pending:
                self.regform.message_pending = message
            case RegistrationState.unpaid:
                self.regform.message_unpaid = message
            case RegistrationState.complete:
                self.regform.message_complete = message
            case _:
                raise ValidationError('Invalid state')
        mock_registration = Registration(state=state, registration_form=self.regform, currency='USD',
                                         email='test@example.com', first_name='Peter', last_name='Higgs',
                                         checked_in=True, friendly_id=-1, event_id=self.event.id,
                                         registration_form_id=self.regform.id)
        for form_item in self.regform.active_fields:
            if form_item.type == RegistrationFormItemType.field_pd and form_item.personal_data_type.column:
                value = getattr(mock_registration, form_item.personal_data_type.column)
            else:
                value = form_item.field_impl.default_value
            if value is NotImplemented:
                continue
            data_entry = RegistrationData()
            mock_registration.data.append(data_entry)
            for attr, field_value in form_item.field_impl.process_form_data(mock_registration, value).items():
                setattr(data_entry, attr, field_value)
        tpl = get_template_module('registration/emails/registration_creation_to_registrant.html',
                                  registration=mock_registration, event=self.event, attach_rejection_reason=True,
                                  old_price=None, diff=None)
        html = render_template('registration/management/email_preview.html', subject=tpl.get_subject(),
                               body=tpl.get_body())
        return jsonify(html=html)


class RHEventRegistrationFormDelete(RegistrationFormDeleteMixin, RHEventManageRegFormBase):
    """Delete a registration form in an event."""


class RHRegistrationFormOpen(RHEventManageRegFormBase):
    """Open registration for a registration form."""

    def _process(self):
        old_dts = (self.regform.start_dt, self.regform.end_dt)
        if self.regform.has_ended:
            self.regform.end_dt = None
        else:
            self.regform.start_dt = now_utc()
        logger.info('Registrations for %s opened by %s', self.regform, session.user)
        flash(_('Registrations for {} are now open').format(self.regform.title), 'success')
        new_dts = (self.regform.start_dt, self.regform.end_dt)
        if new_dts != old_dts:
            if not old_dts[1]:
                log_text = f'Registration form "{self.regform.title}" was opened'
            else:
                log_text = f'Registration form "{self.regform.title}" was reopened'
            self.regform.log(EventLogRealm.event, LogKind.change, 'Registration', log_text, session.user)
        return redirect(url_for('registration_form.manage_regform', self.regform))


class RHRegistrationFormClose(RHEventManageRegFormBase):
    """Close registrations for a registration form."""

    def _process(self):
        close_registration(self.regform)
        flash(_('Registrations for {} are now closed').format(self.regform.title), 'success')
        logger.info('Registrations for %s closed by %s', self.regform, session.user)
        log_text = f'Registration form "{self.regform.title}" was closed'
        self.regform.log(EventLogRealm.event, LogKind.change, 'Registration', log_text, session.user)
        return redirect(url_for('registration_form.manage_regform', self.regform))


class RHRegistrationFormSchedule(RHEventManageRegFormBase):
    """Schedule registrations for a registration form."""

    def _process(self):
        form = RegistrationFormScheduleForm(obj=FormDefaults(self.regform), regform=self.regform)
        if form.validate_on_submit():
            self.regform.start_dt = form.start_dt.data
            self.regform.end_dt = form.end_dt.data
            self.regform.modification_end_dt = form.modification_end_dt.data
            flash(_('Registrations for {} have been scheduled').format(self.regform.title), 'success')
            logger.info('Registrations for %s scheduled by %s', self.regform, session.user)
            log_data = {
                'Start': self.regform.start_dt.isoformat() if self.regform.start_dt else None,
                'End': self.regform.end_dt.isoformat() if self.regform.end_dt else None,
                'Modification End': (self.regform.modification_end_dt.isoformat()
                                     if self.regform.modification_end_dt else None),
            }
            self.regform.log(EventLogRealm.management, LogKind.change, 'Registration',
                             f'Registration form "{self.regform.title}" scheduled', session.user, data=log_data)
            return jsonify_data(flash=False)
        return jsonify_form(form, submit=_('Schedule'))


class RHEventRegistrationFormModify(RegistrationFormModifyMixin, RHEventManageRegFormBase):
    """Modify the form of a registration form for an event."""


class RHRegistrationFormStats(RHEventManageRegFormBase):
    """Display registration form stats page."""

    def _process(self):
        regform_stats = [OverviewStats(self.regform)]
        regform_stats += [AccommodationStats(x) for x in self.regform.active_fields if x.input_type == 'accommodation']
        return WPManageRegistrationStats.render_template('management/regform_stats.html', self.event,
                                                         regform=self.regform, regform_stats=regform_stats)


class RHManageRegistrationManagers(RHEventManageRegFormsBase):
    """Modify event managers with registration role."""

    def _process(self):
        reg_managers = {p.principal for p in self.event.acl_entries
                        if p.has_management_permission('registration', explicit=True)}
        form = RegistrationManagersForm(obj=FormDefaults(managers=reg_managers), event=self.event)
        if form.validate_on_submit():
            update_object_principals(self.event, form.managers.data, permission='registration')
            return jsonify_data(flash=False)
        return jsonify_form(form)


class RHRegistrationFormCreateFromTemplate(RHEventManageRegFormsBase):
    """Create a registration form from a template form."""

    def _process(self):
        form = RegistrationFormCreateFromTemplateForm(event=self.event)
        if form.validate_on_submit():
            title = form.title.data
            regform = form.create_from.data
            new_regform = RegistrationFormCloner.create_from_template(self.event, regform, title)
            signals.event.registration_form_created.send(new_regform)
            flash(_('Registration form has been successfully created'), 'success')
            cloned_from_message = f'"{regform.title}" in category: {regform.category.id}'
            data = {'cloned from': cloned_from_message}
            data.update(_get_regform_creation_log_data(new_regform))
            new_regform.log(EventLogRealm.management, LogKind.positive, 'Registration',
                            f'Registration form "{new_regform.title}" has been created from {cloned_from_message}',
                            session.user, data=data)
            return redirect(url_for('registration_form.manage_regform', new_regform))
        return WPEventManageRegistrationForm.render_template('management/regform_create_from_template.html', self.event,
                                                             form=form, event=self.event)

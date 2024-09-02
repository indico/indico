# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import timedelta
from operator import itemgetter

from flask import flash, redirect, session
from sqlalchemy.orm import undefer
from webargs import fields

from indico.core import signals
from indico.core.db import db
from indico.modules.events.features.util import set_feature_enabled
from indico.modules.events.models.events import EventType
from indico.modules.events.payment import payment_settings
from indico.modules.events.registration import logger, registration_settings
from indico.modules.events.registration.controllers.display import ParticipantListMixin
from indico.modules.events.registration.controllers.management import RHManageRegFormBase, RHManageRegFormsBase
from indico.modules.events.registration.forms import (ParticipantsDisplayForm, ParticipantsDisplayFormColumnsForm,
                                                      RegistrationFormCreateForm, RegistrationFormEditForm,
                                                      RegistrationFormScheduleForm, RegistrationManagersForm)
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.items import PersonalDataType
from indico.modules.events.registration.models.registrations import PublishRegistrationsMode
from indico.modules.events.registration.stats import AccommodationStats, OverviewStats
from indico.modules.events.registration.util import (close_registration, create_personal_data_fields,
                                                     get_flat_section_setup_data)
from indico.modules.events.registration.views import (WPManageParticipants, WPManageRegistration,
                                                      WPManageRegistrationStats)
from indico.modules.events.settings import data_retention_settings
from indico.modules.events.util import update_object_principals
from indico.modules.logs.models.entries import EventLogRealm, LogKind
from indico.modules.users.models.affiliations import Affiliation
from indico.util.date_time import format_human_timedelta, now_utc
from indico.util.i18n import _, force_locale, orig_string
from indico.web.args import use_kwargs
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


class RHManageRegistrationForms(RHManageRegFormsBase):
    """List all registrations forms for an event."""

    def _process(self):
        regforms = (RegistrationForm.query
                    .with_parent(self.event)
                    .options(undefer('active_registration_count'))
                    .order_by(db.func.lower(RegistrationForm.title)).all())
        return WPManageRegistration.render_template('management/regform_list.html', self.event, regforms=regforms)


class RHParticipantListPreview(ParticipantListMixin, RHManageRegFormsBase):
    """Preview the participant list like a registered participant would see it."""

    view_class = WPManageRegistration

    @use_kwargs({'guest': fields.Bool(load_default=False)}, location='query')
    def _process_args(self, guest):
        RHManageRegFormsBase._process_args(self)
        self.preview = 'guest' if guest else 'participant'

    def is_participant(self, user):
        return self.preview == 'participant'


class RHManageRegistrationFormsDisplay(RHManageRegFormsBase):
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


class RHManageRegistrationFormDisplay(RHManageRegFormBase):
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
        return jsonify_template('events/registration/management/regform_display_form_columns.html', form=form,
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


class RHManageParticipants(RHManageRegFormsBase):
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


class RHRegistrationFormCreate(RHManageRegFormsBase):
    """Create a new registration form."""

    def _get_form_defaults(self):
        participant_visibility = (PublishRegistrationsMode.hide_all
                                  if self.event.type_ == EventType.conference
                                  else PublishRegistrationsMode.show_all)
        public_visibility = PublishRegistrationsMode.hide_all
        return FormDefaults(visibility=[participant_visibility.name, public_visibility.name, None])

    def _process(self):
        form = RegistrationFormCreateForm(obj=self._get_form_defaults(), event=self.event)
        if form.validate_on_submit():
            regform = RegistrationForm(event=self.event, currency=payment_settings.get('currency'))
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
            flash(_('Registration form has been successfully created'), 'success')
            regform.log(EventLogRealm.management, LogKind.positive, 'Registration',
                        f'Registration form "{regform.title}" has been created', session.user,
                        data=_get_regform_creation_log_data(regform))
            return redirect(url_for('.manage_regform', regform))
        return WPManageRegistration.render_template('management/regform_create.html', self.event,
                                                    form=form, regform=None)


class RHRegistrationFormManage(RHManageRegFormBase):
    """Specific registration form management."""

    def _process(self):
        return WPManageRegistration.render_template('management/regform.html', self.event, regform=self.regform)


class RHRegistrationFormEdit(RHManageRegFormBase):
    """Edit a registration form."""

    def _get_form_defaults(self):
        return FormDefaults(self.regform, limit_registrations=self.regform.registration_limit is not None)

    def _process(self):
        form = RegistrationFormEditForm(obj=self._get_form_defaults(), event=self.event, regform=self.regform)
        if form.validate_on_submit():
            form.populate_obj(self.regform)
            db.session.flush()
            signals.event.registration_form_edited.send(self.regform)
            flash(_('Registration form has been successfully modified'), 'success')
            return redirect(url_for('.manage_regform', self.regform))
        return WPManageRegistration.render_template('management/regform_edit.html', self.event, form=form,
                                                    regform=self.regform)


class RHRegistrationFormDelete(RHManageRegFormBase):
    """Delete a registration form."""

    def _process(self):
        rels = ('in_attachment_acls', 'in_attachment_folder_acls', 'in_contribution_acls', 'in_event_acls',
                'in_session_acls')
        for rel in rels:
            getattr(self.regform, rel).delete()
        self.regform.is_deleted = True
        signals.event.registration_form_deleted.send(self.regform)
        flash(_('Registration form deleted'), 'success')
        logger.info('Registration form %s deleted by %s', self.regform, session.user)
        self.regform.log(EventLogRealm.management, LogKind.negative, 'Registration',
                         f'Registration form "{self.regform.title}" was deleted', session.user)
        return redirect(url_for('.manage_regform_list', self.event))


class RHRegistrationFormOpen(RHManageRegFormBase):
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
        return redirect(url_for('.manage_regform', self.regform))


class RHRegistrationFormClose(RHManageRegFormBase):
    """Close registrations for a registration form."""

    def _process(self):
        close_registration(self.regform)
        flash(_('Registrations for {} are now closed').format(self.regform.title), 'success')
        logger.info('Registrations for %s closed by %s', self.regform, session.user)
        log_text = f'Registration form "{self.regform.title}" was closed'
        self.regform.log(EventLogRealm.event, LogKind.change, 'Registration', log_text, session.user)
        return redirect(url_for('.manage_regform', self.regform))


class RHRegistrationFormSchedule(RHManageRegFormBase):
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


class RHRegistrationFormModify(RHManageRegFormBase):
    """Modify the form of a registration form."""

    def _process(self):
        min_data_retention = data_retention_settings.get('minimum_data_retention')
        max_data_retention = data_retention_settings.get('maximum_data_retention') or timedelta(days=3650)
        return WPManageRegistration.render_template('management/regform_modify.html', self.event,
                                                    form_data=get_flat_section_setup_data(self.regform),
                                                    regform=self.regform,
                                                    data_retention_range={'min': min_data_retention.days // 7,
                                                                          'max': max_data_retention.days // 7},
                                                    has_predefined_affiliations=Affiliation.query.has_rows())


class RHRegistrationFormStats(RHManageRegFormBase):
    """Display registration form stats page."""

    def _process(self):
        regform_stats = [OverviewStats(self.regform)]
        regform_stats += [AccommodationStats(x) for x in self.regform.active_fields if x.input_type == 'accommodation']
        return WPManageRegistrationStats.render_template('management/regform_stats.html', self.event,
                                                         regform=self.regform, regform_stats=regform_stats)


class RHManageRegistrationManagers(RHManageRegFormsBase):
    """Modify event managers with registration role."""

    def _process(self):
        reg_managers = {p.principal for p in self.event.acl_entries
                        if p.has_management_permission('registration', explicit=True)}
        form = RegistrationManagersForm(obj=FormDefaults(managers=reg_managers), event=self.event)
        if form.validate_on_submit():
            update_object_principals(self.event, form.managers.data, permission='registration')
            return jsonify_data(flash=False)
        return jsonify_form(form)

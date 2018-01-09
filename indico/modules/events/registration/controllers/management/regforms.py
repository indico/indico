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

from operator import attrgetter, itemgetter

from flask import flash, redirect, session
from sqlalchemy.orm import undefer

from indico.core import signals
from indico.core.db import db
from indico.modules.events.features.util import set_feature_enabled
from indico.modules.events.logs.models.entries import EventLogKind, EventLogRealm
from indico.modules.events.models.events import EventType
from indico.modules.events.payment import payment_settings
from indico.modules.events.registration import logger, registration_settings
from indico.modules.events.registration.controllers.management import RHManageRegFormBase, RHManageRegFormsBase
from indico.modules.events.registration.forms import (ParticipantsDisplayForm, ParticipantsDisplayFormColumnsForm,
                                                      RegistrationFormForm, RegistrationFormScheduleForm,
                                                      RegistrationManagersForm)
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.items import PersonalDataType
from indico.modules.events.registration.stats import AccommodationStats, OverviewStats
from indico.modules.events.registration.util import create_personal_data_fields, get_event_section_data
from indico.modules.events.registration.views import (WPManageParticipants, WPManageRegistration,
                                                      WPManageRegistrationStats)
from indico.modules.events.util import update_object_principals
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


class RHManageRegistrationForms(RHManageRegFormsBase):
    """List all registrations forms for an event"""

    def _process(self):
        regforms = (RegistrationForm.query
                    .with_parent(self.event)
                    .options(undefer('active_registration_count'))
                    .order_by(db.func.lower(RegistrationForm.title)).all())
        return WPManageRegistration.render_template('management/regform_list.html', self.event, regforms=regforms)


class RHManageRegistrationFormsDisplay(RHManageRegFormsBase):
    """Customize the display of registrations on the public page"""

    def _process(self):
        regforms = sorted(self.event.registration_forms, key=lambda f: f.title.lower())
        form = ParticipantsDisplayForm()
        if form.validate_on_submit():
            data = form.json.data
            registration_settings.set(self.event, 'merge_registration_forms', data['merge_forms'])
            registration_settings.set_participant_list_form_ids(self.event, data['participant_list_forms'])
            registration_settings.set_participant_list_columns(self.event, data['participant_list_columns'])
            for regform in regforms:
                regform.publish_registrations_enabled = regform.id in data['participant_list_forms']
            flash(_("The participants display settings have been saved."), 'success')
            return redirect(url_for('.manage_regforms_display', self.event))

        available_columns = {field[0].name: field[1]['title'] for field in PersonalDataType.FIELD_DATA}
        enabled_columns = []
        disabled_columns = []
        for column_name in registration_settings.get_participant_list_columns(self.event):
            if column_name in available_columns:
                enabled_columns.append({'id': column_name, 'title': available_columns[column_name]})
                del available_columns[column_name]
        for column_name, column_title in available_columns.iteritems():
            disabled_columns.append({'id': column_name, 'title': column_title})
        disabled_columns.sort(key=itemgetter('title'))

        available_forms = {regform.id: regform for regform in regforms}
        enabled_forms = []
        disabled_forms = []
        # Handle forms that have already been sorted by the user.
        for form_id in registration_settings.get_participant_list_form_ids(self.event):
            try:
                regform = available_forms[form_id]
            except KeyError:
                continue
            # Make sure publication was not disabled since the display settings were modified.
            if regform.publish_registrations_enabled:
                enabled_forms.append(regform)
                del available_forms[form_id]
        for form_id, regform in available_forms.iteritems():
            # There might be forms with publication enabled that haven't been sorted by the user yet.
            if regform.publish_registrations_enabled:
                enabled_forms.append(regform)
            else:
                disabled_forms.append(regform)
        disabled_forms.sort(key=attrgetter('title'))

        merge_forms = registration_settings.get(self.event, 'merge_registration_forms')
        return WPManageRegistration.render_template('management/regform_display.html', self.event,
                                                    regforms=regforms, enabled_columns=enabled_columns,
                                                    disabled_columns=disabled_columns, enabled_forms=enabled_forms,
                                                    disabled_forms=disabled_forms, merge_forms=merge_forms, form=form)


class RHManageRegistrationFormDisplay(RHManageRegFormBase):
    """Choose the columns to be shown on the participant list for a particular form"""

    def _process(self):
        form = ParticipantsDisplayFormColumnsForm()
        if form.validate_on_submit():
            registration_settings.set_participant_list_columns(self.event, form.json.data['columns'], self.regform)
            flash(_('The settings for "{}" have been saved.').format(self.regform.title), 'success')
            return jsonify_data()

        available_fields = {field.id: field for field in self.regform.active_fields}
        enabled_fields = []
        for field_id in registration_settings.get_participant_list_columns(self.event, self.regform):
            try:
                field = available_fields[field_id]
            except KeyError:
                continue
            enabled_fields.append(field)
            del available_fields[field_id]

        disabled_fields = available_fields.values()
        return jsonify_template('events/registration/management/regform_display_form_columns.html', form=form,
                                enabled_columns=enabled_fields, disabled_columns=disabled_fields)


class RHManageParticipants(RHManageRegFormsBase):
    """Show and enable the dummy registration form for participants"""

    def _process_POST(self):
        regform = self.event.participation_regform
        set_feature_enabled(self.event, 'registration', True)
        if not regform:
            regform = RegistrationForm(event=self.event, title="Participants", is_participation=True,
                                       currency=payment_settings.get('currency'))
            create_personal_data_fields(regform)
            db.session.add(regform)
            db.session.flush()
            signals.event.registration_form_created.send(regform)
            self.event.log(EventLogRealm.management, EventLogKind.positive, 'Registration',
                           'Registration form "{}" has been created'.format(regform.title), session.user)
        return redirect(url_for('event_registration.manage_regform', regform))

    def _process_GET(self):
        regform = self.event.participation_regform
        registration_enabled = self.event.has_feature('registration')
        if not regform or not registration_enabled:
            return WPManageParticipants.render_template('management/participants.html', self.event,
                                                        regform=regform, registration_enabled=registration_enabled)
        return redirect(url_for('event_registration.manage_regform', regform))


class RHRegistrationFormCreate(RHManageRegFormsBase):
    """Creates a new registration form"""

    def _process(self):
        form = RegistrationFormForm(event=self.event,
                                    publish_registrations_enabled=(self.event.type_ != EventType.conference))
        if form.validate_on_submit():
            regform = RegistrationForm(event=self.event)
            create_personal_data_fields(regform)
            form.populate_obj(regform)
            db.session.add(regform)
            db.session.flush()
            signals.event.registration_form_created.send(regform)
            flash(_('Registration form has been successfully created'), 'success')
            self.event.log(EventLogRealm.management, EventLogKind.positive, 'Registration',
                           'Registration form "{}" has been created'.format(regform.title), session.user)
            return redirect(url_for('.manage_regform', regform))
        return WPManageRegistration.render_template('management/regform_edit.html', self.event,
                                                    form=form, regform=None)


class RHRegistrationFormManage(RHManageRegFormBase):
    """Specific registration form management"""

    def _process(self):
        return WPManageRegistration.render_template('management/regform.html', self.event, regform=self.regform)


class RHRegistrationFormEdit(RHManageRegFormBase):
    """Edit a registration form"""

    def _get_form_defaults(self):
        return FormDefaults(self.regform, limit_registrations=self.regform.registration_limit is not None)

    def _process(self):
        form = RegistrationFormForm(obj=self._get_form_defaults(), event=self.event)
        if form.validate_on_submit():
            form.populate_obj(self.regform)
            db.session.flush()
            flash(_('Registration form has been successfully modified'), 'success')
            return redirect(url_for('.manage_regform', self.regform))
        return WPManageRegistration.render_template('management/regform_edit.html', self.event, form=form,
                                                    regform=self.regform)


class RHRegistrationFormDelete(RHManageRegFormBase):
    """Delete a registration form"""

    def _process(self):
        self.regform.is_deleted = True
        signals.event.registration_form_deleted.send(self.regform)
        flash(_("Registration form deleted"), 'success')
        logger.info("Registration form %s deleted by %s", self.regform, session.user)
        return redirect(url_for('.manage_regform_list', self.event))


class RHRegistrationFormOpen(RHManageRegFormBase):
    """Opens registration for a registration form"""

    def _process(self):
        if self.regform.has_ended:
            self.regform.end_dt = None
        else:
            self.regform.start_dt = now_utc()
        logger.info("Registrations for %s opened by %s", self.regform, session.user)
        flash(_("Registrations for {} are now open").format(self.regform.title), 'success')
        return redirect(url_for('.manage_regform', self.regform))


class RHRegistrationFormClose(RHManageRegFormBase):
    """Closes registrations for a registration form"""

    def _process(self):
        self.regform.end_dt = now_utc()
        if not self.regform.has_started:
            self.regform.start_dt = self.regform.end_dt
        flash(_("Registrations for {} are now closed").format(self.regform.title), 'success')
        logger.info("Registrations for %s closed by %s", self.regform, session.user)
        return redirect(url_for('.manage_regform', self.regform))


class RHRegistrationFormSchedule(RHManageRegFormBase):
    """Schedules registrations for a registration form"""

    def _process(self):
        form = RegistrationFormScheduleForm(obj=FormDefaults(self.regform), regform=self.regform)
        if form.validate_on_submit():
            self.regform.start_dt = form.start_dt.data
            self.regform.end_dt = form.end_dt.data
            self.regform.modification_end_dt = form.modification_end_dt.data
            flash(_("Registrations for {} have been scheduled").format(self.regform.title), 'success')
            logger.info("Registrations for %s scheduled by %s", self.regform, session.user)
            return jsonify_data(flash=False)
        return jsonify_form(form, submit=_('Schedule'))


class RHRegistrationFormModify(RHManageRegFormBase):
    """Modify the form of a registration form"""

    def _process(self):
        return WPManageRegistration.render_template('management/regform_modify.html', self.event,
                                                    sections=get_event_section_data(self.regform, management=True),
                                                    regform=self.regform)


class RHRegistrationFormStats(RHManageRegFormBase):
    """Display registration form stats page"""

    def _process(self):
        regform_stats = [OverviewStats(self.regform)]
        regform_stats += [AccommodationStats(x) for x in self.regform.active_fields if x.input_type == 'accommodation']
        return WPManageRegistrationStats.render_template('management/regform_stats.html', self.event,
                                                         regform=self.regform, regform_stats=regform_stats)


class RHManageRegistrationManagers(RHManageRegFormsBase):
    """Modify event managers with registration role"""

    def _process(self):
        reg_managers = {p.principal for p in self.event.acl_entries
                        if p.has_management_role('registration', explicit=True)}
        form = RegistrationManagersForm(obj=FormDefaults(managers=reg_managers))
        if form.validate_on_submit():
            update_object_principals(self.event, form.managers.data, role='registration')
            return jsonify_data(flash=False)
        return jsonify_form(form)

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

from flask import redirect, flash, session

from indico.core.db import db
from indico.modules.events.logs.models.entries import EventLogRealm, EventLogKind
from indico.modules.events.registration import logger
from indico.modules.events.registration.controllers.management import (RHManageRegFormBase,
                                                                       RHManageRegFormsBase)
from indico.modules.events.registration.forms import RegistrationFormForm, RegistrationFormScheduleForm
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.util import get_event_section_data, create_personal_data_fields
from indico.modules.events.registration.views import WPManageRegistration
from indico.modules.payment import event_settings
from indico.web.util import jsonify_data, jsonify_template
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.web.forms.base import FormDefaults
from indico.web.flask.util import url_for, url_rule_to_js


class RHManageRegistrationForms(RHManageRegFormsBase):
    """List all registrations forms for an event"""

    def _process(self):
        regforms = (self.event_new.registration_forms
                    .filter_by(is_deleted=False)
                    .order_by(db.func.lower(RegistrationForm.title))
                    .all())
        return WPManageRegistration.render_template('management/regform_list.html', self.event,
                                                    event=self.event, regforms=regforms)


class RHRegistrationFormCreate(RHManageRegFormsBase):
    """Creates a new registration form"""

    def _process(self):
        form = RegistrationFormForm()
        if form.validate_on_submit():
            regform = RegistrationForm(event_new=self.event_new)
            create_personal_data_fields(regform)
            form.populate_obj(regform)
            db.session.add(regform)
            db.session.flush()
            flash(_('Registration form has been successfully created'), 'success')
            self.event.log(EventLogRealm.management, EventLogKind.positive, 'Registration',
                           'Registration form "{}" has been created'.format(regform.title), session.user)
            return redirect(url_for('.manage_regform', regform))
        return WPManageRegistration.render_template('management/regform_edit.html', self.event, event=self.event,
                                                    form=form)


class RHRegistrationFormManage(RHManageRegFormBase):
    """Specific registration form management"""

    def _process(self):
        return WPManageRegistration.render_template('management/regform.html', self.event, regform=self.regform,
                                                    event=self.event)


class RHRegistrationFormEdit(RHManageRegFormBase):
    """Edit a registration form"""

    def _get_form_defaults(self):
        return FormDefaults(self.regform, limit_registrations=self.regform.registration_limit is not None)

    def _process(self):
        form = RegistrationFormForm(obj=self._get_form_defaults())
        if form.validate_on_submit():
            form.populate_obj(self.regform)
            db.session.flush()
            flash(_('Registration form has been successfully modified'), 'success')
            return redirect(url_for('.manage_regform', self.regform))
        return WPManageRegistration.render_template('management/regform_edit.html', self.event, form=form,
                                                    event=self.event, regform=self.regform)


class RHRegistrationFormDelete(RHManageRegFormBase):
    """Delete a registration form"""

    def _process(self):
        self.regform.is_deleted = True
        flash(_("Registration form deleted"), 'success')
        logger.info("Registration form {} deleted by {}".format(self.regform, session.user))
        return redirect(url_for('.manage_regform_list', self.event))


class RHRegistrationFormOpen(RHManageRegFormBase):
    """Opens registration for a registration form"""

    def _process(self):
        if self.regform.has_ended:
            self.regform.end_dt = None
        else:
            self.regform.start_dt = now_utc()
        logger.info("Registrations for {} opened by {}".format(self.regform, session.user))
        flash(_("Registrations for {} are now open").format(self.regform.title), 'success')
        return redirect(url_for('.manage_regform', self.regform))


class RHRegistrationFormClose(RHManageRegFormBase):
    """Closes registrations for a registration form"""

    def _process(self):
        self.regform.end_dt = now_utc()
        if not self.regform.has_started:
            self.regform.start_dt = self.regform.end_dt
        flash(_("Registrations for {} are now closed").format(self.regform.title), 'success')
        logger.info("Registrations for {} closed by {}".format(self.regform, session.user))
        return redirect(url_for('.manage_regform', self.regform))


class RHRegistrationFormSchedule(RHManageRegFormBase):
    """Schedules registrations for a registration form"""

    def _process(self):
        form = RegistrationFormScheduleForm(obj=FormDefaults(self.regform), regform=self.regform)
        if form.validate_on_submit():
            self.regform.start_dt = form.start_dt.data
            self.regform.end_dt = form.end_dt.data
            flash(_("Registrations for {} have been scheduled").format(self.regform.title), 'success')
            logger.info("Registrations for {} scheduled by {}".format(self.regform, session.user))
            return jsonify_data(flash=False)
        return jsonify_template('events/registration/management/regform_schedule.html', form=form)


class RHRegistrationFormModify(RHManageRegFormBase):
    """Modify the form of a registration form"""

    def _process(self):
        return WPManageRegistration.render_template('management/regform_modify.html', self.event, event=self.event_new,
                                                    sections=get_event_section_data(self.regform, management=True),
                                                    regform=self.regform,
                                                    currency=event_settings.get(self.event, 'currency'))

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
from indico.modules.events.registration.forms import RegistrationFormForm
from indico.modules.events.registration.models.registration_forms import RegistrationForm
from indico.modules.events.registration.views import WPManageRegistration
from indico.util.i18n import _
from indico.web.forms.base import FormDefaults
from indico.web.flask.util import url_for


class RHRegistrationFormList(RHManageRegFormsBase):
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
            form.populate_obj(regform)
            db.session.add(regform)
            flash(_('Registration form has been successfully created'), 'success')
            self.event.log(EventLogRealm.management, EventLogKind.positive, 'Registration',
                           'Registration form "{}" has been created'.format(regform.title), session.user)
            return redirect(url_for('.manage_regform_list', self.event_new))
        return WPManageRegistration.render_template('management/regform_edit.html', self.event, event=self.event,
                                                    form=form)


class RHRegistrationFormManage(RHManageRegFormBase):
    """Specific registration form management"""

    def _process(self):
        return WPManageRegistration.render_template('management/regform.html', self.event, regform=self.regform)


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
            return redirect(url_for('.manage_regform_list', self.event_new))
        return WPManageRegistration.render_template('management/regform_edit.html', self.event, form=form,
                                                    event=self.event, regform=self.regform)


class RHRegistrationFormDelete(RHManageRegFormBase):
    """Delete a registration form"""

    def _process(self):
        self.regform.is_deleted = True
        flash(_("Registration form deleted"), 'success')
        logger.info("Registration form {} deleted by {}".format(self.regform, session.user))
        return redirect(url_for('.manage_regform_list', self.event))

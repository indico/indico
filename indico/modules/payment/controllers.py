# This file is part of Indico.
# Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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

from flask import redirect, flash, request

from indico.modules.payment import settings, event_settings
from indico.modules.payment.forms import AdminSettingsForm, EventSettingsForm
from indico.modules.payment.views import WPPaymentAdmin, WPPaymentEventManagement
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from MaKaC.webinterface.rh.admins import RHAdminBase
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHPaymentAdminSettings(RHAdminBase):
    """Payment settings (admin)"""

    def _process(self):
        form = AdminSettingsForm(obj=FormDefaults(**settings.get_all()))
        if form.validate_on_submit():
            settings.set_multi(form.data)
            flash(_('Settings saved'), 'success')
            return redirect(url_for('.admin_settings'))
        return WPPaymentAdmin.render_template('admin_settings.html', form=form)


class RHPaymentEventSettings(RHConferenceModifBase):
    """Payment settings (event)"""

    def _process(self):
        event = self._conf
        currencies = dict(settings.get('currencies'))
        return WPPaymentEventManagement.render_template('event_settings.html', event, event=event,
                                                        settings=event_settings.get_all(event),
                                                        currencies=currencies)


class RHPaymentEventSettingsEdit(RHConferenceModifBase):
    """Edit payment settings (event)"""

    def _process(self):
        event = self._conf
        current_event_settings = event_settings.get_all(event)
        defaults = FormDefaults(current_event_settings, **settings.get_all())
        form = EventSettingsForm(prefix='payment-', obj=defaults, event=event)
        if form.validate_on_submit():
            event_settings.set_multi(event, form.data)
            flash(_('Settings saved'), 'success')
            return redirect(url_for('.event_settings', event))
        return WPPaymentEventManagement.render_template('event_settings_edit.html', event, event=event,
                                                        form=form)


class RHPaymentEventToggle(RHConferenceModifBase):
    """Enable/disable payment for an event"""

    def _process(self):
        event = self._conf
        enabled = request.form['enabled'] == '1'
        if event_settings.get(event, 'enabled', None) is None:
            copy_settings = {'currency', 'conditions', 'summary_email', 'success_email'}
            data = {k: v for k, v in settings.get_all().iteritems() if k in copy_settings}
            event_settings.set_multi(event, data)
        event_settings.set(event, 'enabled', enabled)
        return redirect(url_for('.event_settings', event))

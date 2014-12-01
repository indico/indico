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

from flask import redirect, flash, request, session, jsonify
from werkzeug.exceptions import NotFound

from indico.core.errors import IndicoError
from indico.modules.payment import settings, event_settings
from indico.modules.payment.forms import AdminSettingsForm, EventSettingsForm
from indico.modules.payment.util import get_payment_plugins, get_active_payment_plugins
from indico.modules.payment.views import WPPaymentAdmin, WPPaymentEventManagement, WPPaymentEvent
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from MaKaC.webinterface.rh.admins import RHAdminBase
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.webinterface.rh.registrationFormDisplay import RHRegistrationFormRegistrantBase


class RHPaymentAdminSettings(RHAdminBase):
    """Payment settings (admin)"""

    def _process(self):
        form = AdminSettingsForm(obj=FormDefaults(**settings.get_all()))
        if form.validate_on_submit():
            settings.set_multi(form.data)
            flash(_('Settings saved'), 'success')
            return redirect(url_for('.admin_settings'))
        return WPPaymentAdmin.render_template('admin_settings.html', form=form, plugins=get_payment_plugins().values())


class RHPaymentEventSettings(RHConferenceModifBase):
    """Payment settings (event)"""

    def _process(self):
        event = self._conf
        currencies = {c['code']: c['name'] for c in settings.get('currencies')}
        plugins = get_payment_plugins()
        enabled_plugins = [plugin for plugin in plugins.itervalues() if plugin.event_settings.get(event, 'enabled')]
        return WPPaymentEventManagement.render_template('event_settings.html', event, event=event,
                                                        settings=event_settings.get_all(event),
                                                        currencies=currencies, plugins=plugins.items(),
                                                        enabled_plugins=enabled_plugins)


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
        if enabled and not get_payment_plugins():
            flash(_('There are no payment methods available. Please contact your Indico administrator.'), 'error')
            return redirect(url_for('.event_settings', event))
        if event_settings.get(event, 'enabled', None) is None:
            copy_settings = {'currency', 'conditions', 'summary_email', 'success_email'}
            data = {k: v for k, v in settings.get_all().iteritems() if k in copy_settings}
            event_settings.set_multi(event, data)
        event_settings.set(event, 'enabled', enabled)
        return redirect(url_for('.event_settings', event))


class RHPaymentEventPluginEdit(RHConferenceModifBase):
    """Configure a payment plugin for an event"""

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        try:
            self.plugin = get_payment_plugins()[request.view_args['method']]
        except KeyError:
            raise NotFound

    def _process(self):
        event = self._conf
        can_modify = self.plugin.can_be_modified(session.user, event)
        defaults = FormDefaults(self.plugin.event_settings.get_all(event), **self.plugin.settings.get_all())
        form = self.plugin.event_settings_form(prefix='payment-', obj=defaults)
        if can_modify and form.validate_on_submit():
            self.plugin.event_settings.set_multi(event, form.data)
            flash(_('Settings for {0} saved').format(self.plugin.title), 'success')
            return redirect(url_for('.event_settings', event))
        widget_attrs = {}
        if not can_modify:
            widget_attrs = {field.short_name: {'disabled': True} for field in form}
        return WPPaymentEventManagement.render_template('event_plugin_edit.html', event, event=event, form=form,
                                                        plugin=self.plugin, can_modify=can_modify,
                                                        widget_attrs=widget_attrs)


class RHPaymentEventCheckout(RHRegistrationFormRegistrantBase):
    """Payment/Checkout page for registrants"""

    def _checkParams(self, params):
        RHRegistrationFormRegistrantBase._checkParams(self, params)
        if event_settings.get(self._conf, 'enabled') and params.get("conditions", "false") != "on":
            raise IndicoError("You cannot pay without accepting the conditions")

    def _process(self):
        event = self._conf
        amount = self._registrant.getTotal()
        currency = event_settings.get(event, 'currency')
        plugins = get_active_payment_plugins(event)
        force_plugin = plugins.items()[0] if len(plugins) == 1 else None  # only one plugin available
        return WPPaymentEvent.render_template('event_checkout.html', event, event=event, registrant=self._registrant,
                                              plugins=plugins.items(), force_plugin=force_plugin, amount=amount,
                                              currency=currency)


class RHPaymentEventForm(RHRegistrationFormRegistrantBase):
    """Loads the form for the selected payment plugin"""

    def _checkParams(self, params):
        RHRegistrationFormRegistrantBase._checkParams(self, params)
        try:
            self.plugin = get_payment_plugins()[request.args['method']]
        except KeyError:
            raise NotFound

    def _process(self):
        with self.plugin.plugin_context():
            html = self.plugin.render_payment_form(self._conf, self._registrant, self._registrant.getTotal(),
                                                   event_settings.get(self._conf, 'currency'))
        return jsonify(html=html)

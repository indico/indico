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

import math
from datetime import datetime

from flask import redirect, flash, request, session, jsonify
from werkzeug.exceptions import NotFound

from indico.core.plugins.controllers import RHPluginDetails
from indico.modules.payment import settings, event_settings
from indico.modules.payment.forms import AdminSettingsForm, EventSettingsForm
from indico.modules.payment.util import get_payment_plugins, get_active_payment_plugins, get_registrant_params
from indico.modules.payment.views import WPPaymentAdmin, WPPaymentEventManagement, WPPaymentEvent
from indico.util.i18n import _
from indico.web.flask.util import url_for, redirect_or_jsonify
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


class RHPaymentAdminPluginSettings(RHPluginDetails):
    """Payment plugin settings (admin)"""
    back_button_endpoint = 'payment.admin_settings'


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

    CSRF_ENABLED = True

    def _process(self):
        event = self._conf
        enabled = request.form['enabled'] == '1'
        if enabled and not get_payment_plugins():
            flash(_('There are no payment methods available. Please contact your Indico administrator.'), 'error')
            return redirect(url_for('.event_settings', event))
        if event_settings.get(event, 'enabled', None) is None:
            copy_settings = {'currency', 'conditions', 'register_email', 'success_email'}
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

    def _checkProtection(self):
        self.protection_overridden = False
        can_modify_plugin = session.user and self.plugin.can_be_modified(session.user, self._conf)
        can_modify_event = self._conf.as_event.can_manage(session.user, allow_key=True)
        self.protection_overridden = can_modify_plugin and not can_modify_event
        if not can_modify_plugin and not can_modify_event:
            RHConferenceModifBase._checkProtection(self)
        return True

    def _check_currencies(self, form):
        """Checks if the currencies are valid.

        :return: `(auto_currency, invalid_currency)` - tuple containing the currency that should
                 be automatically set on the event and a flag if the currency issues cannot be resolved
                 automatically and require user interaction (i.e. saving the plugin settings is disallowed)
        """
        messages = []
        event = self._conf
        valid_currencies = self.plugin.valid_currencies
        currency = event_settings.get(event, 'currency')
        if valid_currencies is None or currency in valid_currencies:
            return None, False, messages

        if len(valid_currencies) == 1:
            auto_currency = list(valid_currencies)[0]
            for plugin in get_active_payment_plugins(event).itervalues():
                if plugin.valid_currencies is not None and auto_currency not in plugin.valid_currencies:
                    messages.append(('error', _("This payment method only supports {}, but the payment method "
                                                "'{}' doesn't.").format(auto_currency, plugin.title)))
                    return None, True, messages
            if not form.is_submitted():
                messages.append(('warning', _("This payment method only supports {0}. Enabling it will automatically "
                                              "change the currency of the event to {0}!").format(auto_currency)))
            return auto_currency, False, messages

        if not form.is_submitted():
            messages.append(('error', _("To enable this payment method, please use one of the following "
                                        "currencies: {}").format(', '.join(valid_currencies))))
        return None, True, messages

    def _process(self):
        event = self._conf
        can_modify = session.user and self.plugin.can_be_modified(session.user, event)
        plugin_settings = self.plugin.settings.get_all()
        defaults = FormDefaults(self.plugin.event_settings.get_all(event), **plugin_settings)
        form = self.plugin.event_settings_form(prefix='payment-', obj=defaults, plugin_settings=plugin_settings)
        auto_currency, invalid_currency, messages = self._check_currencies(form)
        if can_modify and form.validate_on_submit() and not invalid_currency:
            self.plugin.event_settings.set_multi(event, form.data)
            flash(_('Settings for {} saved').format(self.plugin.title), 'success')
            if form.enabled.data and auto_currency is not None:
                event_settings.set(event, 'currency', auto_currency)
                flash(_("The event's currency has been changed to {}.").format(auto_currency), 'warning')
            if self.protection_overridden:
                return redirect_or_jsonify(request.url)
            else:
                return redirect_or_jsonify(url_for('.event_settings', event), plugin=self.plugin.name,
                                           enabled=form.enabled.data)
        widget_attrs = {}
        if not can_modify:
            widget_attrs = {field.short_name: {'disabled': True} for field in form}
        return WPPaymentEventManagement.render_template('event_plugin_edit.html', event, event=event, form=form,
                                                        plugin=self.plugin, can_modify=can_modify, messages=messages,
                                                        widget_attrs=widget_attrs, invalid_currency=invalid_currency)


class RHPaymentEventCheckout(RHRegistrationFormRegistrantBase):
    """Payment/Checkout page for registrants"""

    def _process(self):
        if self._registrant.getPayed():
            flash(_('You have already paid for your registration.'), 'info')
            return redirect(url_for('event.confRegistrationFormDisplay', self._conf, **get_registrant_params()))
        checkout_attempt_delta = None
        if not self._registrant.isCheckoutSessionAlive():
            self._registrant._checkout_attempt_dt = datetime.now()
        else:
            checkout_attempt_dt = self._registrant.getCheckoutAttemptDt()
            checkout_attempt_delta = int(math.ceil((datetime.now() - checkout_attempt_dt).total_seconds() / 60))
        event = self._conf
        amount = self._registrant.getTotal()
        currency = event_settings.get(event, 'currency')
        plugins = get_active_payment_plugins(event)
        force_plugin = plugins.items()[0] if len(plugins) == 1 else None  # only one plugin available
        return WPPaymentEvent.render_template('event_checkout.html', event, event=event, registrant=self._registrant,
                                              plugins=plugins.items(), force_plugin=force_plugin, amount=amount,
                                              currency=currency, checkout_attempt_delta=checkout_attempt_delta,
                                              registrant_params=get_registrant_params())


class RHPaymentEventForm(RHRegistrationFormRegistrantBase):
    """Loads the form for the selected payment plugin"""

    def _checkParams(self, params):
        RHRegistrationFormRegistrantBase._checkParams(self, params)
        try:
            self.plugin = get_active_payment_plugins(self._conf)[request.args['method']]
        except KeyError:
            raise NotFound

    def _process(self):
        with self.plugin.plugin_context():
            html = self.plugin.render_payment_form(self._conf, self._registrant, self._registrant.getTotal(),
                                                   event_settings.get(self._conf, 'currency'))
        return jsonify(html=html)

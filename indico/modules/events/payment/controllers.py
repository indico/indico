# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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
from werkzeug.exceptions import NotFound, BadRequest

from indico.core.plugins.controllers import RHPluginDetails
from indico.modules.admin import RHAdminBase
from indico.modules.events.payment import settings, event_settings
from indico.modules.events.payment.forms import AdminSettingsForm, EventSettingsForm
from indico.modules.events.payment.util import get_payment_plugins, get_active_payment_plugins
from indico.modules.events.payment.views import WPPaymentAdmin, WPPaymentEventManagement, WPPaymentEvent
from indico.modules.events.registration.controllers.display import RHRegistrationFormRegistrationBase
from indico.modules.events.registration.models.registrations import RegistrationState
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_template, jsonify_data, jsonify_form
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHPaymentAdminSettings(RHAdminBase):
    """Payment settings in server admin area"""

    def _process(self):
        form = AdminSettingsForm(obj=FormDefaults(**settings.get_all()))
        if form.validate_on_submit():
            settings.set_multi(form.data)
            flash(_('Settings saved'), 'success')
            return redirect(url_for('.admin_settings'))
        return WPPaymentAdmin.render_template('admin_settings.html', form=form, plugins=get_payment_plugins().values())


class RHPaymentAdminPluginSettings(RHPluginDetails):
    """Payment plugin settings in server admin area"""
    back_button_endpoint = 'payment.admin_settings'


class RHPaymentManagementBase(RHConferenceModifBase):
    """Base RH for event management pages"""

    EVENT_FEATURE = 'payment'
    CSRF_ENABLED = True


class RHPaymentBase(RHRegistrationFormRegistrationBase):
    """Base RH for non-management payment pages"""
    EVENT_FEATURE = 'payment'

    def _checkParams(self, params):
        RHRegistrationFormRegistrationBase._checkParams(self, params)
        if self.registration is None:
            raise NotFound


class RHPaymentSettings(RHPaymentManagementBase):
    """Display payment settings"""

    def _process(self):
        methods = get_payment_plugins()
        enabled_methods = [method for method in methods.itervalues()
                           if method.event_settings.get(self.event_new, 'enabled')]
        return WPPaymentEventManagement.render_template('management/payments.html', self._conf, event=self.event_new,
                                                        settings=event_settings.get_all(self.event_new),
                                                        methods=methods.items(), enabled_methods=enabled_methods)


class RHPaymentSettingsEdit(RHPaymentManagementBase):
    """Edit payment settings"""

    def _process(self):
        current_event_settings = event_settings.get_all(self.event_new)
        defaults = FormDefaults(current_event_settings, **settings.get_all())
        form = EventSettingsForm(prefix='payment-', obj=defaults)
        if form.validate_on_submit():
            event_settings.set_multi(self.event_new, form.data)
            flash(_('Settings saved'), 'success')
            return jsonify_data()
        return jsonify_form(form)


class RHPaymentPluginEdit(RHPaymentManagementBase):
    """Configure a payment plugin for an event"""

    def _checkParams(self, params):
        RHPaymentManagementBase._checkParams(self, params)
        try:
            self.plugin = get_payment_plugins()[request.view_args['method']]
        except KeyError:
            raise NotFound

    def _checkProtection(self):
        self.protection_overridden = False
        can_modify_plugin = session.user and self.plugin.can_be_modified(session.user, self.event_new)
        can_modify_event = self.event_new.can_manage(session.user)
        self.protection_overridden = can_modify_plugin and not can_modify_event
        if not can_modify_plugin and not can_modify_event:
            RHPaymentManagementBase._checkProtection(self)
        return True

    def _process(self):
        can_modify = bool(session.user) and self.plugin.can_be_modified(session.user, self.event_new)
        plugin_settings = self.plugin.settings.get_all()
        defaults = FormDefaults(self.plugin.event_settings.get_all(self.event_new), **plugin_settings)
        form = self.plugin.event_settings_form(prefix='payment-', obj=defaults, plugin_settings=plugin_settings)
        if can_modify and form.validate_on_submit():
            self.plugin.event_settings.set_multi(self.event_new, form.data)
            flash(_('Settings for {} saved').format(self.plugin.title), 'success')
            if self.protection_overridden:
                return jsonify_data()
            else:
                return jsonify_data(plugin=self.plugin.name, enabled=form.enabled.data)
        widget_attrs = {}
        if not can_modify:
            widget_attrs = {field.short_name: {'disabled': True} for field in form}
        invalid_regforms = self.plugin.get_invalid_regforms(self.event_new)
        return jsonify_template('events/payment/event_plugin_edit.html', event=self.event_new, form=form,
                                plugin=self.plugin, can_modify=can_modify, widget_attrs=widget_attrs,
                                invalid_regforms=invalid_regforms)


class RHPaymentCheckout(RHPaymentBase):
    """Display payment checkout page"""

    def _process(self):
        if self.registration.state != RegistrationState.unpaid:
            flash(_("The registration doesn't need to be paid"), 'error')
            return redirect(url_for('event_registration.display_regform', self.registration.locator.registrant))
        plugins = get_active_payment_plugins(self.event_new)
        valid_plugins = {k: v for k, v in plugins.iteritems() if v.supports_currency(self.registration.currency)}
        force_plugin = valid_plugins.items()[0] if len(valid_plugins) == 1 else None  # only one plugin available
        return WPPaymentEvent.render_template('event_checkout.html', self._conf, event=self.event_new,
                                              registration=self.registration,
                                              regform=self.registration.registration_form,
                                              plugins=valid_plugins.items(), force_plugin=force_plugin)


class RHPaymentForm(RHPaymentBase):
    """Load the form for the selected payment plugin"""

    def _checkParams(self, params):
        RHPaymentBase._checkParams(self, params)
        try:
            self.plugin = get_active_payment_plugins(self.event_new)[request.args['method']]
        except KeyError:
            raise NotFound
        if not self.plugin.supports_currency(self.registration.currency):
            raise BadRequest("Payment method incompatible with registration currency {}"
                             .format(self.registration.currency))

    def _process(self):
        with self.plugin.plugin_context():
            html = self.plugin.render_payment_form(self.registration)
        return jsonify(html=html)


class RHPaymentConditions(RHConferenceBaseDisplay):
    EVENT_FEATURE = 'payment'

    def _process(self):
        conditions = event_settings.get(self.event_new, 'conditions')
        return WPPaymentEvent.render_template('terms_and_conditions.html', self._conf, conditions=conditions)

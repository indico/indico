# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import re

from flask import render_template, session
from flask_pluginengine import render_plugin_template
from wtforms.fields.core import BooleanField, StringField
from wtforms.validators import DataRequired

from indico.core import signals
from indico.core.config import config
from indico.util.decorators import classproperty
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import IndicoForm
from indico.web.forms.widgets import SwitchWidget


class PaymentPluginSettingsFormBase(IndicoForm):
    method_name = StringField(_('Name'), [DataRequired()],
                              description=_("The name of the payment method displayed to the user."))


class PaymentEventSettingsFormBase(IndicoForm):
    enabled = BooleanField(_('Enabled'),
                           widget=SwitchWidget(),
                           description=_('Only enabled payment methods can be selected by registrants.'))
    method_name = StringField(_('Name'), [DataRequired()],
                              description=_("The name of the payment method displayed to the user."))

    def __init__(self, *args, **kwargs):
        # Provide the plugin settings in case a plugin needs them for more complex form fields.
        self._plugin_settings = kwargs.pop('plugin_settings')
        super(PaymentEventSettingsFormBase, self).__init__(*args, **kwargs)


class PaymentPluginMixin(object):
    settings_form = PaymentPluginSettingsFormBase
    event_settings_form = PaymentEventSettingsFormBase
    #: Set containing all valid currencies. Set to `None` to allow all.
    valid_currencies = None

    def init(self):
        super(PaymentPluginMixin, self).init()
        if not self.name.startswith('payment_'):
            raise Exception('Payment plugins must be named payment_*')
        self.connect(signals.event_management.management_url, self.get_event_management_url)

    @property
    def default_settings(self):
        return {'method_name': self.title}

    @classproperty
    @classmethod
    def category(self):
        from indico.core.plugins import PluginCategory
        return PluginCategory.payment

    @property
    def logo_url(self):
        return config.IMAGES_BASE_URL + '/payment_logo.png'

    def can_be_modified(self, user, event):
        """Check if the user is allowed to enable/disable/modify the payment method.

        :param user: the :class:`.User` repesenting the user
        :param event: the :class:`Event`
        """
        return event.can_manage(user)

    def get_event_management_url(self, event, **kwargs):
        # This is needed only in case a plugin overrides `can_be_modified` and grants access to users who do not have
        # event management access. In this case they should be redirected to the plugin's edit payment page.
        # In the future it might be useful to expose a limited version of the main payment page to those users since
        # right now there is no good way to access both payment methods if there are two of this kind and you have
        # access to both.
        if session.user and self.can_be_modified(session.user, event):
            return url_for('payment.event_plugin_edit', event, method=re.sub(r'^payment_', '', self.name))

    def get_invalid_regforms(self, event):
        """Return registration forms with incompatible currencies."""
        from indico.modules.events.registration.models.forms import RegistrationForm
        invalid_regforms = []
        if self.valid_currencies is not None:
            invalid_regforms = (RegistrationForm.query.with_parent(event)
                                .filter(~RegistrationForm.currency.in_(self.valid_currencies))
                                .all())
        return invalid_regforms

    def supports_currency(self, currency):
        if self.valid_currencies is None:
            return True
        return currency in self.valid_currencies

    def get_method_name(self, event):
        """Return the (customized) name of the payment method."""
        return self.event_settings.get(event, 'method_name')

    def adjust_payment_form_data(self, data):
        """Update the payment form data if necessary.

        This method can be overridden to update e.g. the amount based on choices the user makes
        in the payment form or to provide additional data to the form. To do so, `data` must
        be modified.

        :param data: a dict containing event, registration, amount, currency,
                     settings and event_settings
        """
        pass

    def render_payment_form(self, registration):
        """Return the payment form shown to the user.

        :param registration: a :class:`Registration` object
        """
        event = registration.registration_form.event
        settings = self.settings.get_all()
        event_settings = self.event_settings.get_all(event)
        data = {'event': event,
                'registration': registration,
                'amount': registration.price,
                'currency': registration.currency,
                'settings': settings,
                'event_settings': event_settings}
        self.adjust_payment_form_data(data)
        return render_plugin_template('event_payment_form.html', **data)

    def render_transaction_details(self, transaction):
        """Render the transaction details in event management.

        Override this (or inherit from the template) to show more useful data such as transaction IDs

        :param transaction: the :class:`PaymentTransaction`
        """
        # Try using the template in the plugin first in case it extends the default one
        return render_template(['{}:transaction_details.html'.format(transaction.plugin.name),
                                'events/payment/transaction_details.html'],
                               plugin=transaction.plugin, transaction=transaction)

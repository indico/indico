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
import re

from flask import session
from flask_pluginengine import render_plugin_template
from wtforms.fields.core import StringField, BooleanField
from wtforms.validators import DataRequired

from indico.core import signals
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import IndicoForm
from MaKaC.accessControl import AccessWrapper


class PaymentPluginSettingsFormBase(IndicoForm):
    method_name = StringField(_('Name'), [DataRequired()],
                              description=_("The name of the payment method displayed to the user."))


class PaymentEventSettingsFormBase(IndicoForm):
    enabled = BooleanField(_('Enabled'), description=_('Only enabled payment methods can be selected by registrants.'))
    method_name = StringField(_('Name'), [DataRequired()],
                              description=_("The name of the payment method displayed to the user."))


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

    def can_be_modified(self, user, event):
        """Checks if the user is allowed to enable/disable/modify the payment method.

        :param user: the :class:`Avatar` of the user
        :param event: the :class:`Conference`
        """
        return event.canModify(AccessWrapper(user))

    def get_event_management_url(self, event, **kwargs):
        # This is needed only in case a plugin overrides `can_be_modified` and grants access to users who do not have
        # event management access. In this case they should be redirected to the plugin's edit payment page.
        # In the future it might be useful to expose a limited version of the main payment page to those users since
        # right now there is no good way to access both payment methods if there are two of this kind and you have
        # access to both.
        if self.can_be_modified(session.user, event):
            return url_for('payment.event_plugin_edit', event, method=re.sub(r'^payment_', '', self.name))

    def get_method_name(self, event):
        """Returns the (customized) name of the payment method."""
        return self.event_settings.get(event, 'method_name')

    def render_payment_form(self, event, registrant, amount, currency):
        """Returns the payment form shown to the user.

        :param event: the :class:`Conference`
        :param registrant: the :class:`Registrant`
        :param amount: the amount of money the registrant has to pay
        :param currency: the currency used for the payment
        """
        settings = self.settings.get_all()
        event_settings = self.event_settings.get_all(event)
        return render_plugin_template('event_payment_form.html', event=event, registrant=registrant, amount=amount,
                                      currency=currency, settings=settings, event_settings=event_settings)

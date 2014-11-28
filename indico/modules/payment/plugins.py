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

from flask_pluginengine import render_plugin_template
from wtforms.fields.core import StringField, BooleanField
from wtforms.validators import DataRequired

from indico.util.i18n import _
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

    def init(self):
        super(PaymentPluginMixin, self).init()
        if not self.name.startswith('payment_'):
            raise Exception('Payment plugins must be named payment_*')

    def can_be_modified(self, user, event):
        """Checks if the user is allowed to enable/disable/modify the payment method.

        :param user: the :class:`Avatar` of the user
        :param event: the :class:`Conference`
        """
        return event.canModify(AccessWrapper(user))

    @property
    def default_settings(self):
        return {'method_name': self.title}

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

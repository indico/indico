# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from flask import session

from indico.core import signals
from indico.core.settings import SettingsProxy
from indico.modules.events.features.base import EventFeature
from indico.modules.events.settings import EventSettingsProxy
from indico.modules.events.payment.plugins import (PaymentPluginMixin, PaymentPluginSettingsFormBase,
                                                   PaymentEventSettingsFormBase)
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


__all__ = ('settings', 'event_settings', 'PaymentPluginMixin', 'PaymentPluginSettingsFormBase',
           'PaymentEventSettingsFormBase')

CONDITIONS = ("CANCELLATION:\n"
              "All refunds requests must be in writing by mail to the Conference Secretary as soon as possible.\n"
              "The Conference committee reserves the right to refuse reimbursement of part or all of the fee in the "
              "case of late cancellation. However, each case of cancellation would be considered individually.")


settings = SettingsProxy('payment', {
    'currencies': [{'code': 'EUR', 'name': 'Euro'}, {'code': 'USD', 'name': 'US Dollar'}],
    'currency': 'EUR',
    'conditions': CONDITIONS,
    'checkout_session_timeout': 10
})

event_settings = EventSettingsProxy('payment', {
    'currency': None,
    'conditions': None,
})


@signals.menu.items.connect_via('admin-sidemenu')
def _extend_admin_menu(sender, **kwargs):
    return SideMenuItem('payment', _("Payment"), url_for('payment.admin_settings'), section='customization')


@signals.menu.items.connect_via('event-management-sidemenu')
def _extend_event_management_menu(sender, event, **kwargs):
    if not event.has_feature('payment') or not event.can_manage(session.user, 'registration'):
        return
    return SideMenuItem('payment', _('Payments'), url_for('payment.event_settings', event), section='organization')


@signals.event.get_feature_definitions.connect
def _get_feature_definitions(sender, **kwargs):
    return PaymentFeature


class PaymentFeature(EventFeature):
    name = 'payment'
    friendly_name = _('Payment')
    requires = {'registration'}
    description = _('Gives event managers the opportunity to process payments for registrations.')

    @classmethod
    def enabled(cls, event):
        for setting in ('currency', 'conditions'):
            if event_settings.get(event, setting) is None:
                value = settings.get(setting)
                event_settings.set(event, setting, value)

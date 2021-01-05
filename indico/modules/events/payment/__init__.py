# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import session

from indico.core import signals
from indico.core.settings import SettingsProxy
from indico.modules.events.features.base import EventFeature
from indico.modules.events.payment.plugins import (PaymentEventSettingsFormBase, PaymentPluginMixin,
                                                   PaymentPluginSettingsFormBase)
from indico.modules.events.settings import EventSettingsProxy
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


__all__ = ('payment_settings', 'payment_event_settings', 'PaymentPluginMixin', 'PaymentPluginSettingsFormBase',
           'PaymentEventSettingsFormBase')

CONDITIONS = ("CANCELLATION:\n"
              "All refunds requests must be in writing by mail to the Conference Secretary as soon as possible.\n"
              "The Conference committee reserves the right to refuse reimbursement of part or all of the fee in the "
              "case of late cancellation. However, each case of cancellation would be considered individually.")


payment_settings = SettingsProxy('payment', {
    'currencies': [{'code': 'EUR', 'name': 'Euro'}, {'code': 'USD', 'name': 'US Dollar'}],
    'currency': 'EUR',
    'conditions': CONDITIONS
})

payment_event_settings = EventSettingsProxy('payment', {
    'conditions': None
})


@signals.menu.items.connect_via('admin-sidemenu')
def _extend_admin_menu(sender, **kwargs):
    if session.user.is_admin:
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
    def enabled(cls, event, cloning):
        for setting in ('conditions',):
            if payment_event_settings.get(event, setting) is None:
                value = payment_settings.get(setting)
                payment_event_settings.set(event, setting, value)

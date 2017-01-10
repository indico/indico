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

import re

from indico.core.db import db
from indico.core.plugins import plugin_engine
from indico.modules.events.payment import PaymentPluginMixin
from indico.modules.events.payment.notifications import notify_double_payment
from indico.modules.events.payment.models.transactions import PaymentTransaction, TransactionStatus
from indico.modules.events.registration.notifications import notify_registration_state_update

remove_prefix_re = re.compile('^payment_')


def get_payment_plugins():
    """Returns a dict containing the available payment plugins."""
    return {remove_prefix_re.sub('', p.name): p for p in plugin_engine.get_active_plugins().itervalues()
            if isinstance(p, PaymentPluginMixin)}


def get_active_payment_plugins(event):
    """Returns a dict containing the active payment plugins of an event."""
    return {name: plugin for name, plugin in get_payment_plugins().iteritems()
            if plugin.event_settings.get(event, 'enabled')}


def register_transaction(registration, amount, currency, action, provider=None, data=None):
    """Creates a new transaction for a certain transaction action.

    :param registration: the `Registration` associated to the transaction
    :param amount: the (strictly positive) amount of the transaction
    :param currency: the currency used for the transaction
    :param action: the `TransactionAction` of the transaction
    :param provider: the payment method name of the transaction,
                     or '_manual' if no payment method has been used
    :param data: arbitrary JSON-serializable data specific to the
                 transaction's provider
    """
    new_transaction, double_payment = PaymentTransaction.create_next(registration=registration, action=action,
                                                                     amount=amount, currency=currency,
                                                                     provider=provider, data=data)
    if new_transaction:
        db.session.flush()
        if double_payment:
            notify_double_payment(registration)
        if new_transaction.status == TransactionStatus.successful:
            registration.update_state(paid=True)
        elif new_transaction.status == TransactionStatus.cancelled:
            registration.update_state(paid=False)
        notify_registration_state_update(registration)
        return new_transaction

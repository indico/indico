# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re

from flask import session

from indico.core.db import db
from indico.core.plugins import plugin_engine
from indico.modules.events.payment import PaymentPluginMixin
from indico.modules.events.payment.models.transactions import PaymentTransaction, TransactionAction, TransactionStatus
from indico.modules.events.registration.notifications import notify_registration_state_update


remove_prefix_re = re.compile('^payment_')


def get_payment_plugins():
    """Return a dict containing the available payment plugins."""
    return {remove_prefix_re.sub('', p.name): p for p in plugin_engine.get_active_plugins().values()
            if isinstance(p, PaymentPluginMixin)}


def get_active_payment_plugins(event):
    """Return a dict containing the active payment plugins of an event."""
    return {name: plugin for name, plugin in get_payment_plugins().items()
            if plugin.event_settings.get(event, 'enabled')}


def register_transaction(registration, amount, currency, action, provider=None, data=None):
    """Create a new transaction for a certain transaction action.

    :param registration: the `Registration` associated to the transaction
    :param amount: the (strictly positive) amount of the transaction
    :param currency: the currency used for the transaction
    :param action: the `TransactionAction` of the transaction
    :param provider: the payment method name of the transaction,
                     or ``None`` if no payment method has been used
    :param data: arbitrary JSON-serializable data specific to the
                 transaction's provider
    """
    new_transaction = PaymentTransaction.create_next(registration=registration, action=action,
                                                     amount=amount, currency=currency,
                                                     provider=provider, data=data)
    if new_transaction:
        db.session.flush()
        if new_transaction.status == TransactionStatus.successful:
            registration.update_state(paid=True)
            notify_registration_state_update(registration, from_management=(provider is None))
        elif new_transaction.status == TransactionStatus.cancelled:
            registration.update_state(paid=False)
            notify_registration_state_update(registration, from_management=(provider is None))
        return new_transaction


def toggle_registration_payment(registration, paid):
    """Toggle registration payment.

    :param registration: the `Registration` to be modified
    :param paid: `True` if the registration should be set as paid, `False` otherwise
    """
    currency = registration.currency if paid else registration.transaction.currency
    amount = registration.price if paid else registration.transaction.amount
    action = TransactionAction.complete if paid else TransactionAction.cancel
    register_transaction(registration=registration,
                         amount=amount,
                         currency=currency,
                         action=action,
                         data={'changed_by_name': session.user.full_name,
                               'changed_by_id': session.user.id})

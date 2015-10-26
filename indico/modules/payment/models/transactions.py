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

from flask import render_template
from sqlalchemy.dialects.postgresql import JSON

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.custom.utcdatetime import UTCDateTime
from indico.core.logger import Logger
from indico.util.date_time import now_utc
from indico.util.string import format_repr, return_ascii
from indico.util.struct.enum import IndicoEnum


class InvalidTransactionStatus(Exception):
    pass


class InvalidManualTransactionAction(Exception):
    pass


class InvalidTransactionAction(Exception):
    pass


class IgnoredTransactionAction(Exception):
    pass


class DoublePaymentTransaction(Exception):
    pass


class TransactionAction(int, IndicoEnum):
    complete = 1
    cancel = 2
    pending = 3
    reject = 4


class TransactionStatus(int, IndicoEnum):
    #: payment attempt succeeded
    successful = 1
    #: payment cancelled manually
    cancelled = 2
    #: payment attempt failed
    failed = 3
    #: payment on hold pending approval of merchant
    pending = 4
    #: payment rejected after being pending
    rejected = 5


class TransactionStatusTransition(object):

    initial_statuses = [TransactionStatus.cancelled, TransactionStatus.failed, TransactionStatus.rejected]

    @classmethod
    def next(cls, transaction, action, provider):
        manual_provider = provider == '_manual'
        if not transaction or transaction.status in cls.initial_statuses:
            return cls._next_from_initial(action, manual_provider)
        elif transaction.status == TransactionStatus.successful:
            return cls._next_from_successful(action, manual_provider)
        elif transaction.status == TransactionStatus.pending:
            return cls._next_from_pending(action, manual_provider)
        else:
            raise InvalidTransactionStatus("Invalid transaction status code '{}'".format(transaction.status))

    @staticmethod
    def _next_from_initial(action, manual=False):
        if manual:
            if action == TransactionAction.complete:
                return TransactionStatus.successful
            elif action == TransactionAction.cancel:
                raise IgnoredTransactionAction("Ignored cancel action on initial status")
            else:
                raise InvalidManualTransactionAction(action)
        elif action == TransactionAction.complete:
            return TransactionStatus.successful
        elif action == TransactionAction.pending:
            return TransactionStatus.pending
        elif action == TransactionAction.reject:
            raise IgnoredTransactionAction("Ignored reject action on initial status")
        else:
            raise InvalidTransactionAction(action)

    @staticmethod
    def _next_from_successful(action, manual=False):
        if manual:
            if action == TransactionAction.complete:
                raise IgnoredTransactionAction("Ignored complete action on successful status")
            elif action == TransactionAction.cancel:
                return TransactionStatus.cancelled
            else:
                raise InvalidManualTransactionAction(action)
        elif action == TransactionAction.complete:
            raise DoublePaymentTransaction
        elif action == TransactionAction.pending:
            raise IgnoredTransactionAction("Ignored pending action on successful status")
        elif action == TransactionAction.reject:
            raise IgnoredTransactionAction("Ignored reject action on successful status")
        else:
            raise InvalidTransactionAction(action)

    @staticmethod
    def _next_from_pending(action, manual=False):
        if manual:
            if action == TransactionAction.complete:
                raise IgnoredTransactionAction("Ignored complete action on pending status")
            elif action == TransactionAction.cancel:
                return TransactionStatus.cancelled
            else:
                raise InvalidManualTransactionAction(action)
        elif action == TransactionAction.complete:
            return TransactionStatus.successful
        elif action == TransactionAction.pending:
            raise IgnoredTransactionAction("Ignored pending action on pending status")
        elif action == TransactionAction.reject:
            return TransactionStatus.rejected
        else:
            raise InvalidTransactionAction(action)


class PaymentTransaction(db.Model):
    """Payment transactions"""
    __tablename__ = 'payment_transactions'
    __table_args__ = (db.CheckConstraint('amount > 0', 'positive_amount'),
                      {'schema': 'events'})

    #: Entry ID
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: ID of the associated registration
    registration_id = db.Column(
        db.Integer,
        db.ForeignKey('event_registration.registrations.id'),
        index=True,
        nullable=False
    )
    #: a :class:`TransactionStatus`
    status = db.Column(
        PyIntEnum(TransactionStatus),
        nullable=False
    )
    #: the base amount the user needs to pay (without payment-specific fees)
    amount = db.Column(
        db.Numeric(8, 2),  # max. 999999.99
        nullable=False
    )
    #: the currency of the payment (ISO string, e.g. EUR or USD)
    currency = db.Column(
        db.String,
        nullable=False
    )
    #: the provider of the payment (e.g. manual, PayPal etc.)
    provider = db.Column(
        db.String,
        nullable=False
    )
    #: the date and time the transaction was recorded
    timestamp = db.Column(
        UTCDateTime,
        default=now_utc,
        nullable=False
    )
    #: plugin-specific data of the payment
    data = db.Column(
        JSON,
        nullable=False
    )

    #: The associated registration
    registration = db.relationship(
        'Registration',
        lazy=True,
        foreign_keys=[registration_id],
        backref=db.backref(
            'transactions',
            lazy=True
        )
    )

    @property
    def plugin(self):
        from indico.modules.payment.util import get_payment_plugins
        return get_payment_plugins().get(self.provider)

    @property
    def manual(self):
        return self.provider == '_manual'

    @return_ascii
    def __repr__(self):
        # in case of a new object we might not have the default status set
        status = TransactionStatus(self.status).name if self.status is not None else None
        return format_repr(self, 'id', 'registration_id', 'provider', 'amount', 'currency', 'timestamp', status=status)

    def render_details(self):
        """Renders the transaction details in event management"""
        if self.manual:
            return render_template('payment/transaction_details_manual.html', transaction=self)
        plugin = self.plugin
        if plugin is None:
            return '[plugin not loaded: {}]'.format(self.provider)
        with plugin.plugin_context():
            return plugin.render_transaction_details(self)

    @classmethod
    def create_next(cls, registration, amount, currency, action, provider='_manual', data=None):
        previous_transaction = registration.transaction
        new_transaction = PaymentTransaction(amount=amount, currency=currency,
                                             provider=provider, data=data)
        registration.transaction = new_transaction
        double_payment = False
        try:
            next_status = TransactionStatusTransition.next(previous_transaction, action, provider)
        except InvalidTransactionStatus as e:
            Logger.get('payment').exception("{}\nData received: {}".format(e, data))
            return None, None
        except InvalidManualTransactionAction as e:
            Logger.get('payment').exception("Invalid manual action code '{}' on initial status\n"
                                            "Data received: {}".format(e, data))
            return None, None
        except InvalidTransactionAction as e:
            Logger.get('payment').exception("Invalid action code '{}' on initial status\n"
                                            "Data received: {}".format(e, data))
            return None, None
        except IgnoredTransactionAction as e:
            Logger.get('payment').warning("{}\nData received: {}".format(e, data))
            return None, None
        except DoublePaymentTransaction:
            next_status = TransactionStatus.successful
            double_payment = True
            Logger.get('payment').warning("Received successful payment for an already paid registration")
        new_transaction.status = next_status
        return new_transaction, double_payment

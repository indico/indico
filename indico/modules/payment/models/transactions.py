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

from sqlalchemy.dialects.postgresql import JSON

from indico.core.db import db
from indico.core.db.sqlalchemy.custom.utcdatetime import UTCDateTime
from indico.core.errors import NotFoundError
from indico.core.logger import Logger
from indico.util.date_time import now_utc
from indico.util.string import return_ascii
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
    #: payment attempt failed
    cancelled = 2
    #: payment on hold pending approval of merchant
    failed = 3
    #: payment cancelled manually
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
    __table_args__ = (db.CheckConstraint('status IN ({})'.format(', '.join(map(str, TransactionStatus)))),
                      db.CheckConstraint('amount > 0'),
                      db.UniqueConstraint('event_id', 'registrant_id', 'timestamp'),
                      {'schema': 'events'})

    #: Entry ID
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: ID of the event
    event_id = db.Column(
        db.Integer,
        index=True,
        nullable=False
    )
    #: ID of the registrant
    registrant_id = db.Column(
        db.Integer,
        nullable=False
    )
    #: a :class:`TransactionStatus`
    status = db.Column(
        db.SmallInteger,
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
        index=True,
        nullable=False
    )
    #: plugin-specific data of the payment
    data = db.Column(
        JSON,
        nullable=False
    )

    @property
    def event(self):
        from MaKaC.conference import ConferenceHolder
        return ConferenceHolder().getById(str(self.event_id))

    @property
    def registrant(self):
        return self.event.getRegistrantById(str(self.registrant_id))

    @registrant.setter
    def registrant(self, registrant):
        self.registrant_id = int(registrant.getId())
        self.event_id = int(registrant.getConference().getId())

    @return_ascii
    def __repr__(self):
        # in case of a new object we might not have the default status set
        return '<PaymentTransaction({}, {}, {}, {}, {} {}, {})>'.format(self.event_id, self.registrant_id,
                                                                        TransactionStatus(self.status).name,
                                                                        self.provider, self.amount, self.currency,
                                                                        self.timestamp)

    @classmethod
    def create_next(cls, event_id, registrant_id, amount, currency, action, provider='_manual', data=None):
        from MaKaC.conference import ConferenceHolder
        event = ConferenceHolder().getById(event_id)
        registrant = event.getRegistrantById(registrant_id)
        if not registrant:
            raise NotFoundError("Registrant ID {} doesn't exist in event {}".format(registrant_id, event_id))
        previous_transaction = cls.find_latest_for_registrant(registrant)
        new_transaction = PaymentTransaction(event_id=event_id, registrant_id=registrant_id, amount=amount,
                                             currency=currency, provider=provider, data=data)
        double_payment = False
        try:
            next_status = TransactionStatusTransition.next(previous_transaction, action, provider)
        except InvalidTransactionStatus as e:
            Logger.get('payment').exception(e)
            Logger.get('payment').exception("Data received: {}".format(data))
            return None, None
        except InvalidManualTransactionAction as e:
            Logger.get('payment').exception("Invalid manual action code '{}' on initial status".format(e))
            Logger.get('payment').exception("Data received: {}".format(data))
            return None, None
        except InvalidTransactionAction as e:
            Logger.get('payment').exception("Invalid action code '{}' on initial status".format(e))
            Logger.get('payment').exception("Data received: {}".format(data))
            return None, None
        except IgnoredTransactionAction as e:
            Logger.get('payment').warning(e)
            Logger.get('payment').warning("Data received: {}".format(data))
            return None, None
        except DoublePaymentTransaction:
            next_status = TransactionStatus.successful
            double_payment = True
            Logger.get('payment').warning("Received successful payment for an already paid registrant")
        new_transaction.status = next_status
        return new_transaction, double_payment

    @staticmethod
    def find_latest_for_registrant(registrant):
        return (PaymentTransaction.find(event_id=registrant.getConference().getId(), registrant_id=registrant.getId())
                                  .order_by(PaymentTransaction.timestamp.desc())
                                  .first())

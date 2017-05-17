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
from functools import partial

from indico.core.db import db
from indico.modules.events.models.settings import EventSetting
from indico.modules.events.payment import payment_settings, payment_event_settings
from indico.modules.events.payment.models.transactions import PaymentTransaction, TransactionStatus
from indico.util.console import cformat
from indico.util.date_time import as_utc
from indico.util.struct.iterables import committing_iterator
from indico_zodbimport import Importer
from indico_zodbimport.util import convert_to_unicode


def ensure_tzinfo(dt):
    return as_utc(dt) if dt.tzinfo is None else dt


class PaymentImporter(Importer):
    def has_data(self):
        return PaymentTransaction.query.has_rows()

    def migrate(self):
        self.messages = [cformat("\n%{blue!}Summary")]

        self.migrate_global_settings()
        self.migrate_event_settings()
        self.migrate_transactions()

        print '\n'.join(self.messages)

    def migrate_global_settings(self):
        self.messages.append(cformat("%{magenta!} - Global Payment Settings:"))
        print cformat("%{white!}migrating global payment settings")

        currency_opt = self.zodb_root['plugins']['EPayment']._PluginBase__options['customCurrency']
        payment_settings.delete_all()

        currencies = [{'code': oc['abbreviation'], 'name': oc['name']} for oc in currency_opt._PluginOption__value]

        payment_settings.set('currencies', currencies)
        for currency in currencies:
            print cformat("%{cyan}saving currency: name='{name}', code={code}").format(**currency)

        db.session.commit()

        msg = cformat("%{green!}migration of global payment settings successful\n")
        self.messages.append('    ' + msg)
        print msg

    def migrate_event_settings(self):
        self.messages.append(cformat("%{magenta!} - Event Payment Settings:"))
        print cformat("%{white!}migrating event settings")

        count = 0

        EventSetting.delete_all(payment_event_settings.module)
        for event in committing_iterator(self._iter_events()):
            old_payment = event._modPay
            default_conditions = payment_settings.get('conditions')
            default_register_email = payment_settings.get('register_email')
            default_success_email = payment_settings.get('success_email')
            register_email = getattr(old_payment, 'receiptMsg', default_register_email)
            success_email = getattr(old_payment, 'successMsg', default_success_email)
            conditions = (getattr(old_payment, 'paymentConditions', default_conditions)
                          if (getattr(old_payment, 'paymentConditionsEnabled', False) and
                              convert_to_unicode(getattr(old_payment, 'specificPaymentConditions', '')).strip() == '')
                          else getattr(old_payment, 'specificPaymentConditions', ''))
            # The new messages are shown in an "additional info" section, so the old defaults can always go away
            if convert_to_unicode(register_email) == 'Please, see the summary of your order:':
                register_email = ''
            if convert_to_unicode(success_email) == 'Congratulations, your payment was successful.':
                success_email = ''
            # Get rid of the most terrible part of the old default conditions
            conditions = convert_to_unicode(conditions).replace('CANCELLATION :', 'CANCELLATION:')
            settings = {
                'enabled': getattr(old_payment, 'activated', False),
                'currency': event._registrationForm._currency,
                'conditions': conditions,
                'register_email': register_email,
                'success_email': success_email,
            }
            payment_event_settings.set_multi(event, settings)

            count += 1
            print cformat("%{cyan}<EventSettings(id={id:>6}, enabled={enabled}, "
                          "currency={currency})>").format(id=event.id, **settings)

        msg = cformat("%{green!}migration of {0} event payment settings successful\n").format(count)
        self.messages.append('    ' + msg)
        print msg

    def migrate_transactions(self):
        self.messages.append(cformat("%{magenta!} - Payment Transactions:"))
        print cformat("%{white!}migrating payment transactions")

        count = 0
        errors = 0
        warnings = 0

        for event, registrant, transaction in committing_iterator(self._iter_transactions()):
            try:
                data = self._get_transaction_data(transaction, event)
            except ValueError as e:
                print cformat("%{red!}{0} (evt: {1}, reg: {2})").format(e, event.id, registrant._id)
                errors += 1
                continue

            if data['provider'] == '_manual' and data['amount'] == 0.0:
                print cformat("%{yellow!}Skipping {0[provider]} transaction (evt: {1}, reg: {2}) "
                              "with zero amount: {0[amount]} {0[currency]}").format(data, event.id, registrant._id)
                warnings += 1
                continue

            elif data['amount'] < 0.0:
                print cformat("%{yellow!}Skipping {0[provider]} transaction (evt: {1}, reg: {2}) "
                              "with negative amount: {0[amount]} {0[currency]}").format(data, event.id, registrant._id)
                warnings += 1
                continue

            pt = PaymentTransaction(event_id=int(event.id), registrant_id=int(registrant._id),
                                    status=TransactionStatus.successful, **data)

            count += 1
            print cformat("%{cyan}{0}").format(pt)
            db.session.add(pt)

        if warnings:
            warning_msg = cformat("%{yellow!}There were {0} warnings during the migration "
                                  "of the payment transactions.").format(warnings)
            self.messages.append('    ' + warning_msg)
            print warning_msg

        if errors:
            msg = cformat("%{red!}There were some errors during the migration of the payment transactions.\n"
                          "{0} transactions were not migrated and will be lost.\n").format(errors)
        else:
            msg = cformat("%{green!}migration of {0} payment transactions successful\n").format(count)
        self.messages.append('    ' + '\n    '.join(msg.split('\n')))
        print msg

    def _get_transaction_data(self, ti, event):
        mapping = {
            'TransactionPayLaterMod': self._get_pay_later_data,
            'TransactionCERNYellowPay': self._get_cern_yellow_pay_data,
            'TransactionPayPal': self._get_paypal_data,
            'FIASpayTransaction': partial(self._get_fiaspay_data, event=event),
            'TransactionWorldPay': self._get_worldpay_data
        }

        try:
            method = mapping[ti.__class__.__name__]
        except KeyError:
            raise ValueError('Unknown transaction type: {}'.format(ti.__class__.__name__))

        return method(ti._Data)

    def _get_pay_later_data(self, ti_data):
        return {
            'amount': ti_data['OrderTotal'],
            'currency': ti_data['Currency'],
            'provider': '_manual',
            'data': {'_migrated': True}
        }

    def _get_cern_yellow_pay_data(self, ti_data):
        return {
            'amount': float(ti_data['OrderTotal']),
            'currency': ti_data['Currency'],
            'provider': 'cern',
            'timestamp': ensure_tzinfo(ti_data['payment_date']),
            'data': {
                'BRAND': ti_data.get('PaymentMethod', ''),
                'PAYID': ti_data['TransactionID'],
                '_migrated': True
            }
        }

    def _get_paypal_data(self, ti_data):
        return {
            'amount': float(ti_data['mc_gross']),
            'currency': ti_data['mc_currency'],
            'provider': 'paypal',
            'timestamp': ensure_tzinfo(ti_data['payment_date']),
            'data': {
                'verify_sign': ti_data['verify_sign'],
                'payer_id': ti_data['payer_id'],
                'mc_gross': ti_data['mc_gross'],
                'mc_currency': ti_data['mc_currency'],
                '_migrated': True
            }
        }

    def _get_fiaspay_data(self, ti_data, event):
        if ti_data['amount'] is None:
            raise ValueError('Transaction has None amount')
        return {
            'amount': float(ti_data['amount']),
            'currency': event._registrationForm._currency,
            'provider': '_manual',
            'timestamp': ensure_tzinfo(ti_data['payment_date']),
            'data': {
                'payer_id': ti_data['payer_id'],
                '_migrated': True,
                '_old_provider': 'fiaspay'
            }
        }

    def _get_worldpay_data(self, ti_data):
        return {
            'amount': float(ti_data['amount']),
            'currency': ti_data['currency'],
            'provider': '_manual',
            'timestamp': ensure_tzinfo(ti_data['payment_date']),
            'data': {
                'email': ti_data['email'],
                'transId': ti_data['transId'],
                '_migrated': True,
                '_old_provider': 'worldpay'
            }
        }

    def _iter_events(self):
        currency_re = re.compile('^[A-Z]{3}$')
        for event in self.flushing_iterator(self.zodb_root['conferences'].itervalues()):
            if not hasattr(event, '_modPay') or not hasattr(event, '_registrationForm'):
                continue
            if not currency_re.match(getattr(event._registrationForm, '_currency', '')):
                continue
            yield event

    def _iter_transactions(self):
        for event in self._iter_events():
            for registrant in getattr(event, '_registrants', {}).itervalues():
                transaction = getattr(registrant, '_transactionInfo', None)
                if transaction:
                    yield event, registrant, transaction

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

from flask import render_template

from indico.core.notifications import email_sender, make_email


@email_sender
def notify_double_payment(registration):
    event = registration.registration_form.event
    to = event.as_event.creator.email
    body = render_template('payment/emails/double_payment_email_to_manager.txt', event=event, registration=registration)
    return make_email(to, subject='Double payment detected', body=body)


@email_sender
def notify_amount_inconsistency(registration, amount, currency):
    event = registration.registration_form.event
    to = event.as_event.creator.email
    body = render_template('payment/emails/payment_inconsistency_email_to_manager.txt',
                           event=event, registration=registration, amount=amount, currency=currency)
    return make_email(to, subject='Payment inconsistency', body=body)

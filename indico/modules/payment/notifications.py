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
from indico.modules.payment import event_settings as payment_event_settings
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for


@email_sender
def notify_double_payment(registrant):
    event = registrant.getConference()
    to = event.as_event.creator.email
    body = render_template('payment/emails/double_payment_email_to_manager.txt', event=event, registrant=registrant)
    return make_email(to, subject='Double payment detected', body=body)


@email_sender
def notify_amount_inconsistency(registrant, amount):
    event = registrant.getConference()
    currency = payment_event_settings.get(event, 'currency')
    to = event.as_event.creator.email
    body = render_template('payment/emails/payment_inconsistency_email_to_manager.txt', event=event,
                           registrant=registrant, amount=amount, currency=currency)
    return make_email(to, subject='Payment inconsistency', body=body)


@email_sender
def notify_payment_confirmation(registrant, amount):
    event = registrant.getConference()
    reg_form = registrant.getRegistrationForm()
    from_address = reg_form.getNotificationSender()
    currency = payment_event_settings.get(event, 'currency')

    # Send email to organizers
    notification = reg_form.getNotification()
    to_list = notification.getToList()
    cc_list = notification.getCCList()
    if to_list or cc_list:
        reg_page = url_for('event_mgmt.confModifRegistrants-modification', registrant, _external=True, _secure=True)
        tpl = get_template_module('payment/emails/payment_confirmation_organizers.txt', event=event,
                                  registrant=registrant, amount=amount, currency=currency, reg_page=reg_page)
        yield make_email(to_list, cc_list, from_address=from_address, subject=tpl.get_subject(), body=tpl.get_body())

    # Send email to the registrant
    if reg_form.isSendPaidEmail():
        success_email_msg = payment_event_settings.get(event, 'success_email')
        params = {}
        if not registrant.getAvatar():
            params = {'registrantId': registrant.getId(), 'authkey': registrant.getRandomId()}
        reg_page = url_for('event.confRegistrationFormDisplay', event, _external=True, _secure=True, **params)
        tpl = get_template_module('payment/emails/payment_confirmation_registrant.txt', event=event,
                                  registrant=registrant, amount=amount, currency=currency,
                                  success_email_msg=success_email_msg, reg_page=reg_page)
        yield make_email(registrant.getEmail(), from_address=from_address, subject=tpl.get_subject(),
                         body=tpl.get_body())

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

from indico.core.notifications import email_sender, make_email
from indico.modules.payment import event_settings as payment_event_settings
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for

from MaKaC.PDFinterface.conference import TicketToPDF


@email_sender
def notify_registration_confirmation(event, registrant):
    reg_form = registrant.getRegistrationForm()
    from_address = reg_form.getNotificationSender()

    # Send email to organizers
    notification = reg_form.getNotification()
    to_list = notification.getToList()
    cc_list = notification.getCCList()
    if to_list or cc_list:
        reg_page = url_for('event_mgmt.confModifRegistrants-modification', registrant, _external=True, _secure=True)
        tpl = get_template_module('events/registration/emails/registration_confirmation_organizers.txt', event=event,
                                  registrant=registrant, reg_page=reg_page)
        yield make_email(to_list, cc_list, from_address=from_address, subject=tpl.get_subject(), body=tpl.get_body())

    # Send email to the registrant
    if reg_form.isSendRegEmail():
        needs_to_pay = registrant.doPay() and payment_event_settings.get(event, 'enabled')
        registration_email_msg = payment_event_settings.get(event, 'register_email')
        params = {}
        if not registrant.getAvatar():
            params = {'registrant_id': registrant.getId(), 'authkey': registrant.getRandomId()}
        reg_page = url_for('event.confRegistrationFormDisplay', event, _external=True, _secure=True, **params)
        tpl = get_template_module('events/registration/emails/registration_confirmation_registrant.txt', event=event,
                                  registrant=registrant, payment_enabled=payment_event_settings.get(event, 'enabled'),
                                  reg_page=reg_page, needs_to_pay=needs_to_pay,
                                  registration_email_msg=registration_email_msg)

        ticket = reg_form.getETicket()
        attachment = {}
        if ticket.isEnabled() and ticket.isAttachedToEmail():
            attachment = {
                'name': 'Ticket.pdf',
                'binary': TicketToPDF(event, registrant).getPDFBin()
            }

        yield make_email(registrant.getEmail(), from_address=from_address, subject=tpl.get_subject(),
                         body=tpl.get_body(), attachments=[attachment])


@email_sender
def notify_registration_modification(event, registrant):
    reg_form = registrant.getRegistrationForm()
    from_address = reg_form.getNotificationSender()

    # Send email to organizers
    notification = reg_form.getNotification()
    to_list = notification.getToList()
    cc_list = notification.getCCList()
    if to_list or cc_list:
        reg_page = url_for('event_mgmt.confModifRegistrants-modification', registrant, _external=True, _secure=True)
        tpl = get_template_module('events/registration/emails/registration_modification_organizers.txt', event=event,
                                  registrant=registrant, reg_page=reg_page)
        yield make_email(to_list, cc_list, from_address=from_address, subject=tpl.get_subject(), body=tpl.get_body())

    # Send email to the registrant
    if reg_form.isSendRegEmail():
        needs_to_pay = registrant.doPay() and payment_event_settings.get(event, 'enabled')
        params = {}
        if not registrant.getAvatar():
            params = {'registrant_id': registrant.getId(), 'authkey': registrant.getRandomId()}
        reg_page = url_for('event.confRegistrationFormDisplay', event, _external=True, _secure=True, **params)
        tpl = get_template_module('events/registration/emails/registration_modification_registrant.txt', event=event,
                                  registrant=registrant, payment_enabled=payment_event_settings.get(event, 'enabled'),
                                  reg_page=reg_page, needs_to_pay=needs_to_pay)

        yield make_email(registrant.getEmail(), from_address=from_address, subject=tpl.get_subject(),
                         body=tpl.get_body())

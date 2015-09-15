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

from collections import OrderedDict

from indico.core.notifications import email_sender, make_email
from indico.modules.payment import event_settings as payment_event_settings
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.util.string import to_unicode

from MaKaC.PDFinterface.conference import TicketToPDF
from MaKaC.registration import PersonalDataForm


def _get_reg_details(reg_form, registrant):
    reg_details = {'misc_details': OrderedDict(), 'personal_data': OrderedDict()}
    for section in reg_form.getSortedForms():
        if section.getId() == 'reasonParticipation':
            reg_details['reason'] = registrant.getReasonParticipation()
        elif section.getId() == 'sessions':
            reg_details['sessions_type'] = 'priorities' if section.getType() == '2priorities' else None
            reg_details['sessions'] = [to_unicode(session.getTitle()) for session in registrant.getSessionList()]
        elif section.getId() == 'accommodation' and section.isEnabled():
            accommodation = registrant.getAccommodation()
            if accommodation.getAccommodationType():
                reg_details['accommodation_type'] = accommodation.getAccommodationType().getCaption()
                reg_details['accommodation_arrival'] = accommodation.getArrivalDate().strftime('%d %B %Y')
                reg_details['accommodation_departure'] = accommodation.getDepartureDate().strftime('%d %B %Y')
        elif section.getId() == 'socialEvents' and section.isEnabled():
            reg_details['social'] = {}
            for social_event in registrant.getSocialEvents():
                reg_details['social'][social_event.getCaption()] = social_event.getNoPlaces()
        elif section.getId() == 'furtherInformation':
            pass
        elif section.isEnabled():
            misc = registrant.getMiscellaneousGroupById(section.getId())
            if not misc:
                continue
            title = to_unicode(misc.getTitle())
            fields = OrderedDict()
            for field in section.getSortedFields():
                response_item = misc.getResponseItemById(field.getId())
                if not response_item:
                    continue
                input_field = response_item.getGeneralField().getInput()
                form_field = {'value': response_item.getValue(),
                              'caption': to_unicode(response_item.getCaption())}
                if response_item.isBillable():
                    form_field['price'] = response_item.getPrice()
                    form_field['currency'] = response_item.getCurrency()
                if form_field['value']:
                    try:
                        form_field['value'] = to_unicode(input_field.getValueDisplay(form_field['value']))
                    except Exception:
                        form_field['value'] = to_unicode(form_field['value']).strip()
                fields[field.getId()] = form_field
            if isinstance(section, PersonalDataForm):
                reg_details['personal_data'][title] = fields
            else:
                reg_details['misc_details'][title] = fields
    return reg_details


@email_sender
def notify_registration_confirmation(event, registrant):
    reg_form = registrant.getRegistrationForm()
    from_address = reg_form.getNotificationSender()
    reg_details = _get_reg_details(reg_form, registrant)

    # Send email to organizers
    notification = reg_form.getNotification()
    to_list = notification.getToList()
    cc_list = notification.getCCList()
    if to_list or cc_list:
        reg_page = url_for('event_mgmt.confModifRegistrants-modification', registrant, _external=True, _secure=True)
        tpl = get_template_module('events/registration/emails/registration_confirmation_organizers.html', event=event,
                                  registrant=registrant, reg_page=reg_page, reg_details=reg_details)
        yield make_email(to_list, cc_list, from_address=from_address, subject=tpl.get_subject(), body=tpl.get_body(),
                         html=True)

    # Send email to the registrant
    if reg_form.isSendRegEmail():
        needs_to_pay = registrant.doPay() and payment_event_settings.get(event, 'enabled')
        registration_email_msg = payment_event_settings.get(event, 'register_email')
        params = {'registrantId': registrant.getId(), 'authkey': registrant.getRandomId()}
        reg_page = url_for('event.confRegistrationFormDisplay', event, _external=True, _secure=True, **params)
        tpl = get_template_module('events/registration/emails/registration_confirmation_registrant.html', event=event,
                                  registrant=registrant, payment_enabled=payment_event_settings.get(event, 'enabled'),
                                  reg_page=reg_page, needs_to_pay=needs_to_pay, reg_details=reg_details,
                                  registration_email_msg=registration_email_msg)

        ticket = reg_form.getETicket()
        attachments = []
        if ticket.isEnabled() and ticket.isAttachedToEmail():
            attachments.append({
                'name': 'Ticket.pdf',
                'binary': TicketToPDF(event, registrant).getPDFBin()
            })

        yield make_email(registrant.getEmail(), from_address=from_address, subject=tpl.get_subject(),
                         body=tpl.get_body(), attachments=attachments, html=True)


@email_sender
def notify_registration_modification(event, registrant):
    reg_form = registrant.getRegistrationForm()
    from_address = reg_form.getNotificationSender()
    reg_details = _get_reg_details(reg_form, registrant)

    # Send email to organizers
    notification = reg_form.getNotification()
    to_list = notification.getToList()
    cc_list = notification.getCCList()
    if to_list or cc_list:
        reg_page = url_for('event_mgmt.confModifRegistrants-modification', registrant, _external=True, _secure=True)
        tpl = get_template_module('events/registration/emails/registration_modification_organizers.html', event=event,
                                  registrant=registrant, reg_page=reg_page, reg_details=reg_details)
        yield make_email(to_list, cc_list, from_address=from_address, subject=tpl.get_subject(), body=tpl.get_body(),
                         html=True)

    # Send email to the registrant
    if reg_form.isSendRegEmail():
        needs_to_pay = registrant.doPay() and payment_event_settings.get(event, 'enabled')
        params = {}
        if not registrant.getAvatar():
            params = {'registrantId': registrant.getId(), 'authkey': registrant.getRandomId()}
        reg_page = url_for('event.confRegistrationFormDisplay', event, _external=True, _secure=True, **params)
        tpl = get_template_module('events/registration/emails/registration_modification_registrant.html', event=event,
                                  registrant=registrant, payment_enabled=payment_event_settings.get(event, 'enabled'),
                                  reg_page=reg_page, needs_to_pay=needs_to_pay, reg_details=reg_details)

        yield make_email(registrant.getEmail(), from_address=from_address, subject=tpl.get_subject(),
                         body=tpl.get_body(), html=True)

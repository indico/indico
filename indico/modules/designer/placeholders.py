# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from babel.numbers import format_currency

from indico.modules.events.registration.util import generate_ticket_qr_code
from indico.util.date_time import format_date, format_datetime
from indico.util.i18n import _
from indico.util.placeholders import Placeholder
from indico.util.string import to_unicode


__all__ = ('EventDatesPlaceholder', 'EventDescriptionPlaceholder', 'RegistrationFullNamePlaceholder',
           'EventOrgTextPlaceholder', 'RegistrationFullNameNoTitlePlaceholder', 'RegistrationFullNamePlaceholderB',
           'RegistrationFullNameNoTitlePlaceholderB', 'RegistrationFullNamePlaceholderC',
           'RegistrationFullNameNoTitlePlaceholderC', 'RegistrationFullNamePlaceholderD',
           'RegistrationFullNameNoTitlePlaceholderD', 'RegistrationTitlePlaceholder',
           'RegistrationFirstNamePlaceholder', 'RegistrationLastNamePlaceholder', 'RegistrationTicketQRPlaceholder',
           'RegistrationEmailPlaceholder', 'RegistrationAmountPlaceholder', 'RegistrationPricePlaceholder',
           'RegistrationAffiliationPlaceholder',
           'RegistrationPositionPlaceholder', 'RegistrationAddressPlaceholder', 'RegistrationCountryPlaceholder',
           'RegistrationPhonePlaceholder', 'EventTitlePlaceholder', 'CategoryTitlePlaceholder', 'EventRoomPlaceholder',
           'EventVenuePlaceholder', 'EventSpeakersPlaceholder')


GROUP_TITLES = {
    'registrant': _("Registrant Data"),
    'event': _("Event Data")
}


class DesignerPlaceholder(Placeholder):
    #: The group of the placeholder. Must be a valid key from `GROUP_TITLES`.
    group = None
    #: Whether the placeholder can only be added to a template by an admin
    admin_only = False
    #: Whether a template containing this placeholder is considered a ticket
    is_ticket = False


class RegistrationPlaceholder(DesignerPlaceholder):
    group = 'registrant'

    @classmethod
    def render(cls, registration):
        return getattr(registration, cls.field)


class RegistrationPDPlaceholder(DesignerPlaceholder):
    group = 'registrant'

    @classmethod
    def render(cls, registration):
        return registration.get_personal_data().get(cls.field) or ''


class FullNamePlaceholderBase(DesignerPlaceholder):
    group = 'registrant'
    name_options = None

    @classmethod
    def render(cls, registration):
        name = (registration.get_personal_data().get('title', '') + ' ') if cls.with_title else ''
        name += registration.get_full_name(**cls.name_options)
        return name


class EventDatesPlaceholder(DesignerPlaceholder):
    group = 'event'
    name = 'event_dates'
    description = _("Event Dates")

    @classmethod
    def render(cls, event):
        start_dt, end_dt = event.start_dt_local, event.end_dt_local
        interval = _("{} to {}").format(to_unicode(format_date(start_dt, format='long')),
                                        to_unicode(format_date(end_dt, format='long')))
        if start_dt.date() == end_dt.date():
            interval = to_unicode(format_datetime(start_dt))
        elif start_dt.date().replace(day=1) == end_dt.date().replace(day=1):
            interval = "{} - {} {}".format(start_dt.day, end_dt.day,
                                           to_unicode(format_date(start_dt, format='MMMM yyyy')))
        return interval


class EventTitlePlaceholder(DesignerPlaceholder):
    group = 'event'
    name = 'event_title'
    description = _("Event Title")

    @classmethod
    def render(cls, event):
        return event.title


class EventDescriptionPlaceholder(DesignerPlaceholder):
    group = 'event'
    name = 'event_description'
    description = _("Event Description")

    @classmethod
    def render(cls, event):
        return event.description


class EventSpeakersPlaceholder(DesignerPlaceholder):
    group = 'event'
    name = 'event_speakers'
    description = _("Event Speakers/Chairs")

    @classmethod
    def render(cls, event):
        return ', '.join(p.full_name for p in event.person_links)


class EventVenuePlaceholder(DesignerPlaceholder):
    group = 'event'
    name = 'event_venue'
    description = _("Event Venue")

    @classmethod
    def render(cls, event):
        return event.venue_name


class EventRoomPlaceholder(DesignerPlaceholder):
    group = 'event'
    name = 'event_room'
    description = _("Event Room")

    @classmethod
    def render(cls, event):
        return event.room_name


class EventOrgTextPlaceholder(DesignerPlaceholder):
    group = 'event'
    name = 'event_organizers'
    description = _("Event Organizers")

    @classmethod
    def render(cls, event):
        return event.organizer_info


class CategoryTitlePlaceholder(DesignerPlaceholder):
    group = 'event'
    name = 'category_title'
    description = _("Category Title")

    @classmethod
    def render(cls, event):
        return event.category.title


class RegistrationFullNamePlaceholder(FullNamePlaceholderBase):
    name = 'full_name'
    description = _("Full Name")
    with_title = True
    name_options = {}


class RegistrationFullNameNoTitlePlaceholder(FullNamePlaceholderBase):
    name = 'full_name_no_title'
    description = _("Full Name (no title)")
    with_title = False
    name_options = {}


class RegistrationFullNamePlaceholderB(FullNamePlaceholderBase):
    name = 'full_name_b'
    description = _("Full Name B")
    with_title = True
    name_options = {'last_name_first': False}


class RegistrationFullNameNoTitlePlaceholderB(FullNamePlaceholderBase):
    name = 'full_name_b_no_title'
    description = _("Full Name B (no title)")
    with_title = False
    name_options = {'last_name_first': False}


class RegistrationFullNamePlaceholderC(FullNamePlaceholderBase):
    name = 'full_name_c'
    description = _("Full Name C")
    with_title = True
    name_options = {'last_name_first': False, 'last_name_upper': True}


class RegistrationFullNameNoTitlePlaceholderC(FullNamePlaceholderBase):
    name = 'full_name_no_title_c'
    description = _("Full Name C (no title)")
    with_title = False
    name_options = {'last_name_upper': True}


class RegistrationFullNamePlaceholderD(FullNamePlaceholderBase):
    name = 'full_name_d'
    description = _("Full Name D (abbrev.)")
    with_title = True
    name_options = {'last_name_first': False, 'last_name_upper': True, 'abbrev_first_name': True}


class RegistrationFullNameNoTitlePlaceholderD(FullNamePlaceholderBase):
    name = 'full_name_no_title_d'
    description = _("Full Name D (abbrev., no title)")
    with_title = False
    name_options = {'last_name_upper': True, 'abbrev_first_name': True}


class RegistrationTitlePlaceholder(RegistrationPDPlaceholder):
    name = 'title'
    description = _("Title")
    field = 'title'


class RegistrationFirstNamePlaceholder(RegistrationPlaceholder):
    name = 'first_name'
    description = _("First Name")
    field = 'first_name'


class RegistrationLastNamePlaceholder(RegistrationPlaceholder):
    name = 'last_name'
    description = _("Last Name")
    field = 'last_name'


class RegistrationEmailPlaceholder(RegistrationPlaceholder):
    name = 'email'
    description = _("E-mail")
    field = 'email'


class RegistrationAmountPlaceholder(RegistrationPlaceholder):
    name = 'amount'
    description = _("Price (no currency)")

    @classmethod
    def render(cls, registration):
        # XXX: Use event locale once we have such a setting
        return format_currency(registration.price, '', locale='en_GB')


class RegistrationPricePlaceholder(RegistrationPlaceholder):
    name = 'price'
    description = _("Price (with currency)")

    @classmethod
    def render(cls, registration):
        # XXX: Use event locale once we have such a setting
        return format_currency(registration.price, registration.currency, locale='en_GB')


class RegistrationAffiliationPlaceholder(RegistrationPDPlaceholder):
    name = 'affiliation'
    description = _("Institution")
    field = 'affiliation'


class RegistrationPositionPlaceholder(RegistrationPDPlaceholder):
    name = 'position'
    description = _("Position")
    field = 'position'


class RegistrationAddressPlaceholder(RegistrationPDPlaceholder):
    name = 'address'
    description = _("Address")
    field = 'address'


class RegistrationCountryPlaceholder(RegistrationPDPlaceholder):
    name = 'country'
    description = _("Country")
    field = 'country'


class RegistrationPhonePlaceholder(RegistrationPDPlaceholder):
    name = 'phone'
    description = _("Phone")
    field = 'phone'


class RegistrationTicketQRPlaceholder(DesignerPlaceholder):
    group = 'registrant'
    name = 'ticket_qr_code'
    description = _("Ticket QR Code")
    is_ticket = True

    @classmethod
    def render(cls, registration):
        return generate_ticket_qr_code(registration)

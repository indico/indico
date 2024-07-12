# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from io import BytesIO

from babel.numbers import format_currency

from indico.modules.designer.models.images import DesignerImageFile
from indico.modules.events.registration.util import generate_ticket_qr_code
from indico.util.date_time import format_date, format_datetime, format_interval
from indico.util.i18n import _
from indico.util.placeholders import Placeholder
from indico.util.string import format_full_name


__all__ = ('EventDatesPlaceholder', 'EventDescriptionPlaceholder', 'RegistrationFullNamePlaceholder',
           'EventOrgTextPlaceholder', 'RegistrationFullNameNoTitlePlaceholder', 'RegistrationFullNamePlaceholderB',
           'RegistrationFullNameNoTitlePlaceholderB', 'RegistrationFullNamePlaceholderC',
           'RegistrationFullNameNoTitlePlaceholderC', 'RegistrationFullNamePlaceholderD',
           'RegistrationFullNameNoTitlePlaceholderD', 'RegistrationTitlePlaceholder',
           'RegistrationFirstNamePlaceholder', 'RegistrationLastNamePlaceholder',
           'RegistrationLastNameUpperPlaceholder', 'RegistrationTicketQRPlaceholder',
           'RegistrationEmailPlaceholder', 'RegistrationAmountPlaceholder', 'RegistrationPricePlaceholder',
           'RegistrationFriendlyIDPlaceholder', 'RegistrationAffiliationPlaceholder',
           'RegistrationPositionPlaceholder', 'RegistrationAddressPlaceholder', 'RegistrationCountryPlaceholder',
           'RegistrationPhonePlaceholder', 'EventTitlePlaceholder', 'CategoryTitlePlaceholder', 'EventRoomPlaceholder',
           'EventVenuePlaceholder', 'EventSpeakersPlaceholder', 'EventLogoPlaceholder', 'FixedTextPlaceholder',
           'FixedImagePlaceholder', 'RegistrationAccompanyingPersonsCountPlaceholder', 'RegistrationPicturePlaceholder',
           'RegistrationAccompanyingPersonsPlaceholder', 'RegistrationAccompanyingPersonsAbbrevPlaceholder')


GROUPS = {
    'event': {'title': _('Event Data'), 'position': 1},
    'fixed': {'title': _('Fixed Data'), 'position': 2},
    'registrant': {'title': _('Common Registrant Data'), 'position': 3},
    'regform_fields': {'title': _('Custom Registrant Data'), 'position': 4},
}


class DesignerPlaceholder(Placeholder):
    #: The group of the placeholder. Must be a valid key from `GROUPS`.
    group = None
    #: Data source for the placeholder.
    data_source = None
    #: Whether the placeholder can only be added to a template by an admin
    admin_only = False
    #: Whether a template containing this placeholder is considered a ticket
    is_ticket = False
    #: Whether this placeholder is rendering an image
    is_image = False


class PersonPlaceholder(DesignerPlaceholder):
    group = 'registrant'
    data_source = 'person'

    @classmethod
    def render(cls, person):
        return person.get(cls.field, '')


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
    data_source = 'person'
    name_options = None

    @classmethod
    def render(cls, person):
        title = ''
        if cls.with_title and not person['is_accompanying']:
            title = person['registration'].get_personal_data().get('title', '')
        name_options = dict(cls.name_options)
        name_options.setdefault('last_name_upper', False)
        name_options.setdefault('abbrev_first_name', False)
        return format_full_name(person['first_name'], person['last_name'], title=title, **name_options)


class EventLogoPlaceholder(DesignerPlaceholder):
    group = 'event'
    name = 'event_logo'
    description = _('Event Logo')
    is_image = True

    @classmethod
    def render(cls, event):
        if not event.has_logo:
            return ''
        return BytesIO(event.logo)


class EventDatesPlaceholder(DesignerPlaceholder):
    group = 'event'
    name = 'event_dates'
    description = _('Event Dates')

    @classmethod
    def render(cls, event):
        start_dt, end_dt = event.start_dt_local, event.end_dt_local
        interval = _('{} to {}').format(format_date(start_dt, format='long'), format_date(end_dt, format='long'))
        if start_dt.date() == end_dt.date():
            interval = format_datetime(start_dt)
        elif start_dt.date().replace(day=1) == end_dt.date().replace(day=1):
            interval = format_interval(start_dt, end_dt, 'dMMMMy')
        return interval


class EventTitlePlaceholder(DesignerPlaceholder):
    group = 'event'
    name = 'event_title'
    description = _('Event Title')

    @classmethod
    def render(cls, event):
        return event.title


class EventDescriptionPlaceholder(DesignerPlaceholder):
    group = 'event'
    name = 'event_description'
    description = _('Event Description')

    @classmethod
    def render(cls, event):
        return event.description


class EventSpeakersPlaceholder(DesignerPlaceholder):
    group = 'event'
    name = 'event_speakers'
    description = _('Event Speakers/Chairs')

    @classmethod
    def render(cls, event):
        return ', '.join(p.full_name for p in event.person_links)


class EventVenuePlaceholder(DesignerPlaceholder):
    group = 'event'
    name = 'event_venue'
    description = _('Event Venue')

    @classmethod
    def render(cls, event):
        return event.venue_name


class EventRoomPlaceholder(DesignerPlaceholder):
    group = 'event'
    name = 'event_room'
    description = _('Event Room')

    @classmethod
    def render(cls, event):
        return event.room_name


class EventOrgTextPlaceholder(DesignerPlaceholder):
    group = 'event'
    name = 'event_organizers'
    description = _('Event Organizers')

    @classmethod
    def render(cls, event):
        return event.organizer_info


class CategoryTitlePlaceholder(DesignerPlaceholder):
    group = 'event'
    name = 'category_title'
    description = _('Category Title')

    @classmethod
    def render(cls, event):
        return event.category.title if not event.is_unlisted else ''


class RegistrationFullNamePlaceholder(FullNamePlaceholderBase):
    name = 'full_name'
    description = _('Full Name')
    with_title = True
    name_options = {}


class RegistrationFullNameNoTitlePlaceholder(FullNamePlaceholderBase):
    name = 'full_name_no_title'
    description = _('Full Name (no title)')
    with_title = False
    name_options = {}


class RegistrationFullNamePlaceholderB(FullNamePlaceholderBase):
    name = 'full_name_b'
    description = _('Full Name B')
    with_title = True
    name_options = {'last_name_first': False}


class RegistrationFullNameNoTitlePlaceholderB(FullNamePlaceholderBase):
    name = 'full_name_b_no_title'
    description = _('Full Name B (no title)')
    with_title = False
    name_options = {'last_name_first': False}


class RegistrationFullNamePlaceholderC(FullNamePlaceholderBase):
    name = 'full_name_c'
    description = _('Full Name C')
    with_title = True
    name_options = {'last_name_first': False, 'last_name_upper': True}


class RegistrationFullNameNoTitlePlaceholderC(FullNamePlaceholderBase):
    name = 'full_name_no_title_c'
    description = _('Full Name C (no title)')
    with_title = False
    name_options = {'last_name_upper': True}


class RegistrationFullNamePlaceholderD(FullNamePlaceholderBase):
    name = 'full_name_d'
    description = _('Full Name D (abbrev.)')
    with_title = True
    name_options = {'last_name_first': False, 'last_name_upper': True, 'abbrev_first_name': True}


class RegistrationFullNameNoTitlePlaceholderD(FullNamePlaceholderBase):
    name = 'full_name_no_title_d'
    description = _('Full Name D (abbrev., no title)')
    with_title = False
    name_options = {'last_name_upper': True, 'abbrev_first_name': True}


class RegistrationTitlePlaceholder(RegistrationPDPlaceholder):
    name = 'title'
    description = _('Title')
    field = 'title'


class RegistrationFirstNamePlaceholder(PersonPlaceholder):
    name = 'first_name'
    description = _('First Name')
    field = 'first_name'


class RegistrationLastNamePlaceholder(PersonPlaceholder):
    name = 'last_name'
    description = _('Last Name')
    field = 'last_name'


class RegistrationLastNameUpperPlaceholder(PersonPlaceholder):
    name = 'last_name_upper'
    description = _('Last Name (uppercase)')
    field = 'last_name'

    @classmethod
    def render(cls, person):
        return super().render(person).upper()


class RegistrationEmailPlaceholder(RegistrationPlaceholder):
    name = 'email'
    description = _('E-mail')
    field = 'email'


class RegistrationAmountPlaceholder(RegistrationPlaceholder):
    name = 'amount'
    description = _('Price (no currency)')

    @classmethod
    def render(cls, registration):
        # XXX: Use event locale once we have such a setting
        return format_currency(registration.price, '', locale='en_GB')


class RegistrationPricePlaceholder(RegistrationPlaceholder):
    name = 'price'
    description = _('Price (with currency)')

    @classmethod
    def render(cls, registration):
        # XXX: Use event locale once we have such a setting
        return format_currency(registration.price, registration.currency, locale='en_GB')


class RegistrationAccompanyingPersonsCountPlaceholder(RegistrationPlaceholder):
    name = 'num_accompanying_persons'
    description = _('Number of accompanying persons')

    @classmethod
    def render(cls, registration):
        return str(registration.num_accompanying_persons)


class AccompanyinPersonsPlaceholderBase(RegistrationPlaceholder):
    name_options = None

    @classmethod
    def render(cls, registration):
        names = [format_full_name(p['firstName'], p['lastName'], **cls.name_options)
                 for p in registration.accompanying_persons]
        return ', '.join(names)


class RegistrationAccompanyingPersonsPlaceholder(AccompanyinPersonsPlaceholderBase):
    name = 'accompanying_persons'
    description = _('Accompanying persons')
    name_options = {'abbrev_first_name': False, 'last_name_first': False}


class RegistrationAccompanyingPersonsAbbrevPlaceholder(AccompanyinPersonsPlaceholderBase):
    name = 'accompanying_persons_abbrev'
    description = _('Accompanying persons (abbrev.)')
    name_options = {'last_name_first': False}


class RegistrationFriendlyIDPlaceholder(RegistrationPlaceholder):
    name = 'registration_friendly_id'
    description = _('Registration ID')
    field = 'friendly_id'


class RegistrationAffiliationPlaceholder(RegistrationPDPlaceholder):
    name = 'affiliation'
    description = _('Institution')
    field = 'affiliation'


class RegistrationPositionPlaceholder(RegistrationPDPlaceholder):
    name = 'position'
    description = _('Position')
    field = 'position'


class RegistrationAddressPlaceholder(RegistrationPDPlaceholder):
    name = 'address'
    description = _('Address')
    field = 'address'


class RegistrationCountryPlaceholder(RegistrationPDPlaceholder):
    name = 'country'
    description = _('Country')
    field = 'country'


class RegistrationPhonePlaceholder(RegistrationPDPlaceholder):
    name = 'phone'
    description = _('Phone')
    field = 'phone'


class RegistrationPicturePlaceholder(RegistrationPDPlaceholder):
    name = 'picture'
    description = _('Picture')
    is_image = True

    @classmethod
    def render(cls, registration):
        if picture_data := registration.get_personal_data_picture():
            with picture_data.open() as fd:
                return BytesIO(fd.read())
        return None


class RegistrationTicketQRPlaceholder(DesignerPlaceholder):
    group = 'registrant'
    data_source = 'person'
    name = 'ticket_qr_code'
    description = _('Ticket QR Code')
    is_ticket = True
    is_image = True

    @classmethod
    def render(cls, person):
        return generate_ticket_qr_code(person)


class FixedTextPlaceholder(DesignerPlaceholder):
    group = 'fixed'
    name = 'fixed'
    description = _('Fixed Text')

    @classmethod
    def render(cls, item):
        return item.get('text', cls.description)


class FixedImagePlaceholder(DesignerPlaceholder):
    group = 'fixed'
    name = 'fixed_image'
    description = _('Fixed Image')
    is_image = True

    @classmethod
    def render(cls, item):
        with DesignerImageFile.get(item['image_id']).open() as fd:
            return BytesIO(fd.read())


class RegistrationFormFieldPlaceholder(DesignerPlaceholder):
    """Placeholder representing a `RegistrationData` instance for a given regform field.

    Unlike other placeholders which are always present, registration data depends
    on the linked regform and thus the placeholders must be generated on the fly.
    """

    group = 'regform_fields'

    def __init__(self, field):
        self.field = field
        self.name = f'field-{field.id}'
        self.is_image = self.field.input_type == 'picture'

    @property
    def description(self):
        return self.field.title

    def render(self, registration):
        data_by_field = registration.data_by_field
        data = data_by_field.get(self.field.id, None)
        if data is None:
            return ''
        return self._render(data)

    def _render(self, data):
        if self.is_image:
            return self._render_image(data)

        friendly_data = data.friendly_data
        if friendly_data is None:
            return ''

        if self.field.input_type in ('multi_choice', 'sessions'):
            return ' · '.join(friendly_data)
        elif self.field.input_type == 'accommodation':
            return self._render_accommodation(friendly_data)
        else:
            return friendly_data

    def _render_image(self, data):
        if data.storage_file_id is not None:
            with data.open() as fd:
                return BytesIO(fd.read())

    def _render_accommodation(self, friendly_data):
        if friendly_data['is_no_accommodation']:
            return _('No accommodation')

        arrival = format_date(friendly_data['arrival_date'])  # TODO: include locale
        departure = format_date(friendly_data['departure_date'])
        accommodation = friendly_data['choice']
        return f'{accommodation} ({arrival} - {departure})'

    @classmethod
    def from_designer_item(cls, regform, item):
        """Create an instance of this class from a designer item."""
        type_ = item['type']
        try:
            field_id = int(type_.removeprefix('field-'))
        except ValueError:
            raise ValueError(f'Invalid field type: {type_}')

        field = next((field for field in regform.active_fields if field.id == field_id), None)
        if not field:
            return None
        return cls(field=field)

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

import mimetypes
import re
from collections import defaultdict
from contextlib import contextmanager
from copy import deepcopy
from datetime import timedelta, datetime
from decimal import Decimal
from HTMLParser import HTMLParser
from operator import attrgetter
from uuid import uuid4

import pytz
from babel.dates import get_timezone
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.attributes import flag_modified

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime, PyIntEnum
from indico.modules.events import Event
from indico.modules.events.models.settings import EventSetting
from indico.modules.events.features.util import set_feature_enabled
from indico.modules.events.layout.models.menu import MenuEntry
from indico.modules.events.registration.models.form_fields import (RegistrationFormPersonalDataField,
                                                                   RegistrationFormField, RegistrationFormFieldData)
from indico.modules.events.registration.models.forms import RegistrationForm, ModificationMode
from indico.modules.events.registration.models.items import (RegistrationFormSection, PersonalDataType,
                                                             RegistrationFormPersonalDataSection, RegistrationFormText)
from indico.modules.events.registration.models.legacy_mapping import LegacyRegistrationMapping
from indico.modules.events.registration.models.registrations import Registration, RegistrationState, RegistrationData
from indico.modules.events.payment.models.transactions import TransactionStatus, PaymentTransaction
from indico.modules.users import User
from indico.util.caching import memoize
from indico.util.console import verbose_iterator, cformat
from indico.util.date_time import now_utc
from indico.util.fs import secure_filename
from indico.util.string import normalize_phone_number, format_repr
from indico.util.struct.iterables import committing_iterator
from indico.web.flask.templating import strip_tags

from indico_zodbimport import Importer, convert_to_unicode
from indico_zodbimport.util import LocalFileImporterMixin

WHITESPACE_RE = re.compile(r'\s+')


@memoize
def _sanitize(string, html=False):
    string = convert_to_unicode(string)
    if not html:
        string = HTMLParser().unescape(strip_tags(string))
    return WHITESPACE_RE.sub(' ', string).strip()


def get_input_type_id(input):
    return {
        'LabelInput': 'label',
        'CheckboxInput': 'checkbox',
        'YesNoInput': 'yes/no',
        'FileInput': 'file',
        'RadioGroupInput': 'radio',
        'CountryInput': 'country',
        'DateInput': 'date',
        'TextInput': 'text',
        'TelephoneInput': 'telephone',
        'TextareaInput': 'textarea',
        'NumberInput': 'number'
    }[input.__class__.__name__]


class OldPaymentTransaction(db.Model):
    __tablename__ = 'payment_transactions_old'
    __table_args__ = {'schema': 'events'}

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer)
    registrant_id = db.Column(db.Integer)
    status = db.Column(PyIntEnum(TransactionStatus))
    amount = db.Column(db.Numeric(8, 2))
    currency = db.Column(db.String)
    provider = db.Column(db.String)
    timestamp = db.Column(UTCDateTime)
    data = db.Column(JSON)

    def __repr__(self):
        return format_repr(self, 'id', 'registrant_id', 'status', 'provider', 'amount', 'currency', 'timestamp')


class RegformMigration(object):
    def __init__(self, importer, event, old_regform):
        self.importer = importer
        self.event = event
        self.old_regform = old_regform
        self.regform = None
        self.transactions = defaultdict(list)
        self.section_map = {}
        self.field_map = {}
        self.status_map = {}
        self.emails = set()
        self.price_adjusted_versions = {}
        self.accommodation_field = None
        self.accommodation_choice_map = {}
        self.social_events_field = None
        self.social_events_choice_map = {}
        self.social_events_info_map = {}
        self.social_events_versions = {}
        self.reason_field = None
        self.multi_session_field = None
        self.specific_session_fields = None
        self.session_choices = None
        self.session_choice_map = {}
        self.session_extra_choice_versions = None
        self.session_extra_choice_map = None
        self.users = set()
        self.past_event = self.event.endDate < now_utc()

    def __repr__(self):
        return 'RegformMigration({})'.format(self.event)

    def run(self):
        self._load_transactions()
        self.regform = RegistrationForm(event_id=int(self.event.id), base_price=0)
        self._migrate_settings()
        self.importer.print_success(cformat('%{blue!}{}%{reset} - %{cyan}{}').format(self.regform.start_dt.date(),
                                                                                     self.regform.title),
                                    event_id=self.event.id)
        self._migrate_form()
        self._migrate_custom_statuses()
        self._migrate_registrations()

    def _load_transactions(self):
        query = (OldPaymentTransaction
                 .find(event_id=self.event.id)
                 .order_by(OldPaymentTransaction.registrant_id, OldPaymentTransaction.timestamp))
        for txn in query:
            self.transactions[txn.registrant_id].append(txn)

    def _migrate_settings(self):
        old_rf = self.old_regform
        self.regform.title = _sanitize(old_rf.title)
        self.regform.introduction = _sanitize(old_rf.announcement)
        self.regform.contact_info = _sanitize(old_rf.contactInfo)
        self.regform.start_dt = self._convert_dt(old_rf.startRegistrationDate)
        self.regform.end_dt = self._convert_dt(old_rf.endRegistrationDate)
        self.regform.modification_mode = ModificationMode.allowed_always
        self.regform.require_login = getattr(old_rf, '_mandatoryAccount', False)
        self.regform.registration_limit = old_rf.usersLimit if old_rf.usersLimit > 0 else None
        self.regform.notification_sender_address = convert_to_unicode(getattr(old_rf, '_notificationSender', None))
        self.regform.manager_notification_recipients = sorted(set(old_rf.notification._ccList) |
                                                              set(old_rf.notification._toList))
        self.regform.manager_notifications_enabled = bool(self.regform.manager_notification_recipients)
        self.regform.publish_registrations_enabled = int(self.event.id) not in self.importer.participant_list_disabled

        old_messages = self.importer.all_payment_settings.get(int(self.event.id))
        if old_messages:
            self.regform.message_unpaid = old_messages.get('register_email', '')
            self.regform.message_complete = old_messages.get('success_email', '')
        old_eticket = getattr(old_rf, '_eTicket', None)
        if old_eticket:
            self.regform.tickets_enabled = old_eticket._enabled
            self.regform.ticket_on_email = old_eticket._attachedToEmail
            self.regform.ticket_on_summary_page = old_eticket._showAfterRegistration
            self.regform.ticket_on_event_page = old_eticket._showInConferenceMenu
        if hasattr(old_rf, 'modificationEndDate'):
            modification_end_dt = self._convert_dt(old_rf.modificationEndDate) if old_rf.modificationEndDate else None
            if modification_end_dt and modification_end_dt > self.regform.end_dt:
                self.regform.modification_end_dt = modification_end_dt

    def _migrate_form(self):
        for form in self.old_regform._sortedForms:
            type_ = form.__class__.__name__
            if type_ == 'PersonalDataForm':
                self._migrate_personal_data_section(form)
            elif type_ == 'GeneralSectionForm':
                self._migrate_general_section(form)
            elif type_ == 'FurtherInformationForm':
                self._migrate_further_info_section(form)
            elif type_ == 'ReasonParticipationForm':
                self._migrate_reason_section(form)
            elif type_ == 'AccommodationForm':
                self._migrate_accommodation_section(form)
            elif type_ == 'SocialEventForm':
                self._migrate_social_event_section(form)
            elif type_ == 'SessionsForm':
                self._migrate_sessions_section(form)
            else:
                raise TypeError('Unhandled section: ' + type_)

    def _migrate_sessions_section(self, form):
        if not form._enabled and not any(x._sessions for x in self.event._registrants.itervalues()):
            return
        section = RegistrationFormSection(registration_form=self.regform, title=_sanitize(form._title),
                                          description=_sanitize(form._description, html=True))
        self.importer.print_info(cformat('%{green!}Section/Sessions%{reset} - %{cyan}{}').format(section.title))
        field_data = {
            'with_extra_slots': False,
            'choices': []
        }
        for sess in form._sessions.itervalues():
            # we intentionally use a static uuid even if we have two fields.
            # this way we don't have to bother with per-field choice mappings
            uuid = unicode(uuid4())
            data = {'price': 0, 'is_billable': False, 'is_enabled': True, 'caption': _sanitize(sess._session.title),
                    'id': uuid}
            if form._type != '2priorities':
                data['is_billable'], data['price'] = self._convert_billable(sess)
            field_data['choices'].append(data)
            self.session_choice_map[sess] = uuid
        self.session_choices = field_data['choices']
        if form._type == '2priorities':
            field_data['item_type'] = 'dropdown'
            field_data['default_item'] = None
            # primary choice
            field = RegistrationFormField(registration_form=self.regform, input_type='single_choice',
                                          title='Preferred choice', is_required=True)
            field.data, field.versioned_data = field.field_impl.process_field_data(field_data)
            section.children.append(field)
            # secondary choice
            field2 = RegistrationFormField(registration_form=self.regform, input_type='single_choice',
                                           title='Secondary choice')
            field2.data, field2.versioned_data = field2.field_impl.process_field_data(field_data)
            section.children.append(field2)
            self.specific_session_fields = (field, field2)
        else:
            # multi-choice field
            field = self.multi_session_field = RegistrationFormField(registration_form=self.regform, title='Sessions',
                                                                     input_type='multi_choice')
            field.data, field.versioned_data = field.field_impl.process_field_data(field_data)
            section.children.append(field)

    def _migrate_social_event_section(self, form):
        if not form._enabled and not any(x._socialEvents for x in self.event._registrants.itervalues()):
            return
        section = RegistrationFormSection(registration_form=self.regform, title=_sanitize(form._title),
                                          description=_sanitize(form._description, html=True))
        self.importer.print_info(cformat('%{green!}Section/Social%{reset} - %{cyan}{}').format(section.title))
        input_type = 'multi_choice' if getattr(form, '_selectionType', 'multiple') == 'multiple' else 'single_choice'
        field_data = {'with_extra_slots': True, 'choices': []}
        if input_type == 'single_choice':
            field_data['item_type'] = 'radiogroup'
            field_data['default_item'] = None
        for item in form._socialEvents.itervalues():
            uuid = unicode(uuid4())
            billable, price = self._convert_billable(item)
            extra_slots_pay = bool(getattr(item, '_pricePerPlace', False))
            field_data['choices'].append({
                'price': price,
                'is_billable': billable,
                'places_limit': int(getattr(item, '_placesLimit', 0)),
                'is_enabled': not bool(getattr(item, '_cancelled', True)),
                'max_extra_slots': int(item._maxPlacePerRegistrant),
                'extra_slots_pay': extra_slots_pay,
                'caption': _sanitize(item._caption),
                'id': uuid
            })
            self.social_events_choice_map[item] = uuid
            self.social_events_info_map[item] = (billable, price, extra_slots_pay)

        field = self.social_events_field = RegistrationFormField(registration_form=self.regform, input_type=input_type,
                                                                 title=section.title,
                                                                 description=_sanitize(form._introSentence),
                                                                 is_required=bool(getattr(form, '_mandatory', False)))
        field.data, field.versioned_data = field.field_impl.process_field_data(field_data)
        section.children.append(field)

    def _migrate_accommodation_section(self, form):
        if not form._enabled and all(x._accommodation._accommodationType is None
                                     for x in self.event._registrants.itervalues()):
            return
        arrival_offset = getattr(form, '_arrivalOffsetDates', [-2, 0])
        departure_offset = getattr(form, '_departureOffsetDates', [1, 3])
        data = {
            'arrival_date_from': (self.event.startDate + timedelta(days=arrival_offset[0])).strftime('%Y-%m-%d'),
            'arrival_date_to': (self.event.startDate + timedelta(days=arrival_offset[1])).strftime('%Y-%m-%d'),
            'departure_date_from': (self.event.endDate + timedelta(days=departure_offset[0])).strftime('%Y-%m-%d'),
            'departure_date_to': (self.event.endDate + timedelta(days=departure_offset[1])).strftime('%Y-%m-%d'),
            'captions': {}
        }
        versioned_data = {'choices': []}
        for item in form._accommodationTypes.itervalues():
            uuid = unicode(uuid4())
            billable, price = self._convert_billable(item)
            data['captions'][uuid] = _sanitize(item._caption)
            versioned_data['choices'].append({
                'price': price,
                'is_billable': billable,
                'places_limit': int(getattr(item, '_placesLimit', 0)),
                'is_enabled': not getattr(item, '_cancelled', False),
                'id': uuid
            })
            self.accommodation_choice_map[item] = uuid

        section = RegistrationFormSection(registration_form=self.regform, title=_sanitize(form._title),
                                          description=_sanitize(form._description, html=True))
        self.importer.print_info(cformat('%{green!}Section/Accommodation%{reset} - %{cyan}{}').format(section.title))
        field = self.accommodation_field = RegistrationFormField(registration_form=self.regform, title=section.title,
                                                                 input_type='accommodation')
        field.data = data
        field.versioned_data = versioned_data
        section.children.append(field)

    def _migrate_reason_section(self, form):
        if not form._enabled and not any(x._reasonParticipation for x in self.event._registrants.itervalues()):
            return
        section = RegistrationFormSection(registration_form=self.regform, title=_sanitize(form._title),
                                          description=_sanitize(form._description, html=True))
        self.importer.print_info(cformat('%{green!}Section/Reason%{reset} - %{cyan}{}').format(section.title))
        field = self.reason_field = RegistrationFormField(registration_form=self.regform, title='Reason',
                                                          input_type='textarea')
        field.data, field.versioned_data = field.field_impl.process_field_data({'number_of_rows': 4})
        section.children.append(field)

    def _migrate_further_info_section(self, form):
        if not form._content or not form._enabled:
            return
        section = RegistrationFormSection(registration_form=self.regform, title=_sanitize(form._title))
        self.importer.print_info(cformat('%{green!}Section/Info%{reset} - %{cyan}{}').format(section.title))
        text = RegistrationFormText(registration_form=self.regform, title='Information',
                                    description=_sanitize(form._content, html=True))
        section.children.append(text)

    def _migrate_personal_data_section(self, form):
        pd_type_map = {
            'email': PersonalDataType.email,
            'firstName': PersonalDataType.first_name,
            'surname': PersonalDataType.last_name,
            'institution': PersonalDataType.affiliation,
            'title': PersonalDataType.title,
            'address': PersonalDataType.address,
            'phone': PersonalDataType.phone,
            'country': PersonalDataType.country,
            'position': PersonalDataType.position
        }
        section = RegistrationFormPersonalDataSection(registration_form=self.regform, title=_sanitize(form._title),
                                                      description=_sanitize(form._description, html=True))
        self.importer.print_info(cformat('%{green!}Section/Personal%{reset} - %{cyan}{}').format(section.title))
        self.section_map[form] = section
        for f in getattr(form, '_sortedFields', []) or getattr(form, '_fields', []):
            old_pd_type = getattr(f, '_pdField', None)
            pd_type = pd_type_map.get(old_pd_type)
            field = self._migrate_field(f, pd_type)
            section.children.append(field)

    def _migrate_general_section(self, form):
        section = RegistrationFormSection(registration_form=self.regform, title=_sanitize(form._title),
                                          description=_sanitize(form._description, html=True),
                                          is_enabled=getattr(form, '_enabled', True))
        self.importer.print_info(cformat('%{green!}Section%{reset} - %{cyan}{}').format(section.title))
        self.section_map[form] = section
        for f in getattr(form, '_sortedFields', []) or getattr(form, '_fields', []):
            section.children.append(self._migrate_field(f))
        return section

    def _migrate_deleted_field(self, old_field):
        try:
            section = self.section_map[old_field._parent]
        except KeyError:
            section = self._migrate_general_section(old_field._parent)
            section.is_deleted = True
        field = self._migrate_field(old_field)
        field.is_deleted = True
        section.children.append(field)
        return field

    def _migrate_field(self, old_field, pd_type=None):
        if get_input_type_id(old_field._input) == 'label':
            text = RegistrationFormText(registration_form=self.regform, title=_sanitize(old_field._caption),
                                        description=_sanitize(getattr(old_field, '_description', '')))
            billable, price = self._convert_billable(old_field)
            if billable and price:
                self.regform.base_price += Decimal(price)
            self.importer.print_info(cformat('%{green}Text%{reset} - %{cyan}{}').format(text.title))
            return text
        field_cls = RegistrationFormPersonalDataField if pd_type is not None else RegistrationFormField
        pd_required = pd_type is not None and pd_type.is_required
        is_required = bool(old_field._mandatory or pd_required)
        is_enabled = bool(not getattr(old_field, '_disabled', False) or pd_required)
        field = field_cls(registration_form=self.regform, personal_data_type=pd_type, is_required=is_required,
                          is_enabled=is_enabled, title=_sanitize(old_field._caption),
                          description=_sanitize(getattr(old_field, '_description', '')))
        self._migrate_field_input(field, old_field, pd_type)
        self.importer.print_info(cformat('%{green}Field/{}%{reset} - %{cyan}{}').format(field.input_type, field.title))
        self.field_map[old_field] = field
        return field

    def _migrate_field_input(self, field, old_field, pd_type):
        field_data = {}
        field_billable = False
        field_places_limit = False
        inp = old_field._input
        old_type = get_input_type_id(inp)
        if pd_type == PersonalDataType.email:
            input_type = 'email'
        elif old_type in {'text', 'country', 'file'}:
            input_type = old_type
        elif old_type == 'textarea':
            input_type = 'textarea'
            field_data['number_of_rows'] = int(getattr(inp, '_numberOfRows', None) or 3)
            field_data['number_of_columns'] = int(getattr(inp, '_numberOfColumns', None) or 60)
        elif old_type == 'number':
            input_type = 'number'
            field_billable = True
            field_data['min_value'] = int(getattr(inp, '_minValue', 0))
        elif old_type == 'radio':
            input_type = 'single_choice'
            field_data['item_type'] = getattr(inp, '_inputType', 'dropdown')
            field_data['with_extra_slots'] = False
            field_data['default_item'] = None
            field_data['choices'] = []
            items = inp._items.itervalues() if hasattr(inp._items, 'itervalues') else inp._items
            for item in items:
                uuid = unicode(uuid4())
                billable, price = self._convert_billable(item)
                field_data['choices'].append({
                    'price': price,
                    'is_billable': billable,
                    'places_limit': int(getattr(item, '_placesLimit', 0)),
                    'is_enabled': bool(getattr(item, '_enabled', True)),
                    'caption': _sanitize(item._caption),
                    'id': uuid
                })
                if item._caption == getattr(inp, '_defaultItem', None):
                    field_data['default_item'] = uuid
        elif old_type == 'checkbox':
            input_type = 'checkbox'
            field_billable = True
            field_places_limit = True
        elif old_type == 'yes/no':
            input_type = 'bool'
            field_billable = True
            field_places_limit = True
        elif old_type == 'date':
            input_type = 'date'
            field_data['date_format'] = inp.dateFormat
        elif old_type == 'telephone':
            input_type = 'phone'
        else:
            raise ValueError('Unexpected field type: ' + old_type)
        field.input_type = input_type
        if field_billable:
            field_data['is_billable'], field_data['price'] = self._convert_billable(old_field)
        if field_places_limit:
            field_data['places_limit'] = int(getattr(old_field, '_placesLimit', 0))
        field.data, field.versioned_data = field.field_impl.process_field_data(field_data)

    def _migrate_custom_statuses(self):
        statuses = getattr(self.old_regform, '_statuses', None)
        if not statuses:
            return
        section = RegistrationFormSection(registration_form=self.regform, is_manager_only=True, title='Custom Statuses',
                                          description='Custom registration statuses (only visible to managers)')
        for status in statuses.itervalues():
            self.status_map[status] = {'field': None, 'choices': {}}
            default = None
            choices = []
            for v in status._statusValues.itervalues():
                uuid = unicode(uuid4())
                if v is status._defaultValue:
                    default = uuid
                caption = _sanitize(v._caption)
                self.status_map[status]['choices'][v] = {'uuid': uuid, 'caption': caption}
                choices.append({'price': 0, 'is_billable': False, 'places_limit': 0, 'is_enabled': True,
                                'caption': caption, 'id': uuid})
            data = {
                'item_type': 'dropdown',
                'with_extra_slots': False,
                'default_item': default,
                'choices': choices
            }
            field = RegistrationFormField(registration_form=self.regform, parent=section, input_type='single_choice',
                                          title=_sanitize(status._caption))
            field.data, field.versioned_data = field.field_impl.process_field_data(data)
            self.status_map[status]['field'] = field

    def _convert_dt(self, naive_dt):
        return get_timezone(self.event.getTimezone()).localize(naive_dt).astimezone(pytz.utc)

    def _convert_billable(self, item):
        try:
            price = float(str(item._price).replace(',', '.')) if getattr(item, '_price', 0) else 0
        except ValueError:
            self.importer.print_warning(cformat('Setting invalid price %{red}{!r}%{reset} to %{green}0%{reset}')
                                        .format(item._price), event_id=self.event.id)
            return False, 0
        return bool(getattr(item, '_billable', False)), price

    def _migrate_registrations(self):
        for old_reg in sorted(self.event._registrants.itervalues(), key=attrgetter('_id')):
            self.regform.registrations.append(self._migrate_registration(old_reg))

    def _migrate_registration(self, old_reg):
        registration = Registration(first_name=convert_to_unicode(old_reg._firstName),
                                    last_name=convert_to_unicode(old_reg._surname),
                                    email=self._fix_email(old_reg._email),
                                    submitted_dt=getattr(old_reg, '_registrationDate', self.regform.start_dt),
                                    base_price=0, price_adjustment=0,
                                    checked_in=getattr(old_reg, '_checkedIn', False))
        # set `checked_in_dt` after initialization since `checked_in` sets it to current dt automatically
        registration.checked_in_dt = getattr(old_reg, '_checkInDate', None)
        # the next two columns break when testing things locally with an existing
        # db, but both can be safely commented out without causing any issues
        registration.friendly_id = int(old_reg._id)
        registration.ticket_uuid = getattr(old_reg, '_checkInUUID', None)
        self.importer.print_info(cformat('%{yellow}Registration%{reset} - %{cyan}{}%{reset} [{}]').format(
            registration.full_name, old_reg._id))
        self._migrate_registration_user(old_reg, registration)
        self._migrate_registration_fields(old_reg, registration)
        self._migrate_registration_accommodation(old_reg, registration)
        self._migrate_registration_social_events(old_reg, registration)
        self._migrate_registration_reason(old_reg, registration)
        self._migrate_registration_sessions(old_reg, registration)
        self._migrate_registration_statuses(old_reg, registration)
        self._migrate_registration_transactions(old_reg, registration)
        # adjust price if necessary
        old_price = Decimal(str(getattr(old_reg, '_total', 0))).max(0)  # negative prices are garbage
        calc_price = registration.price
        registration.price_adjustment = old_price - calc_price
        if registration.price_adjustment:
            self.importer.print_warning('Price mismatch: {} (calculated) != {} (saved). Setting adjustment of {}'
                                        .format(calc_price, old_price, registration.price_adjustment),
                                        event_id=self.event.id)
            assert registration.price == old_price
        # set the registration state
        if (not registration.price or
                (registration.transaction and registration.transaction.status == TransactionStatus.successful)):
            registration.state = RegistrationState.complete
        else:
            registration.state = RegistrationState.unpaid
        # create the legacy mapping
        if hasattr(old_reg, '_randomId'):
            registration.legacy_mapping = LegacyRegistrationMapping(
                event_id=self.event.id,
                legacy_registrant_id=int(old_reg._id),
                legacy_registrant_key=convert_to_unicode(old_reg._randomId)
            )
        return registration

    def _fix_email(self, email):
        email = convert_to_unicode(email).lower()
        try:
            user, host = email.split('@', 1)
        except ValueError:
            self.importer.print_warning(
                cformat('Garbage email %{red}{0}%{reset}; using %{green}{0}@example.com%{reset} instead').format(email),
                event_id=self.event.id)
            user = email
            host = 'example.com'
            email += '@example.com'
        n = 1
        while email in self.emails:
            email = '{}+{}@{}'.format(user, n, host)
            n += 1
        if n != 1:
            self.importer.print_warning(
                cformat('Duplicate email %{yellow}{}@{}%{reset}; using %{green}{}%{reset} instead').format(user, host,
                                                                                                           email),
                event_id=self.event.id)
        self.emails.add(email)
        return email

    def _migrate_registration_user(self, old_reg, registration):
        user = self.importer.all_users_by_email.get(registration.email)
        if user is not None:
            if user in self.users:
                self.importer.print_warning(cformat('User {} is already associated with a registration; not '
                                                    'associating them with {}').format(user, registration),
                                            event_id=self.event.id)
                return
            self.users.add(user)
            registration.user = user
        if not self.past_event and old_reg._avatar and old_reg._avatar.user:
            if not registration.user:
                self.importer.print_warning(cformat('No email match; discarding association between {} and {}')
                                            .format(old_reg._avatar.user, registration), event_id=self.event.id)
            elif registration.user != old_reg._avatar.user:
                self.importer.print_warning(cformat('Email matches other user; associating {} with {} instead of {}')
                                            .format(registration, registration.user, old_reg._avatar.user),
                                            event_id=self.event.id)

    def _migrate_registration_transactions(self, old_reg, registration):
        txn = None
        for old_txn in self.transactions[int(old_reg._id)]:
            if not self.importer.quiet:
                self.importer.print_info(cformat('%{red!}TXN%{reset} %{cyan}{}').format(old_txn))
            txn = PaymentTransaction(registration=registration, status=old_txn.status, amount=old_txn.amount,
                                     currency=old_txn.currency, provider=old_txn.provider, timestamp=old_txn.timestamp,
                                     data=old_txn.data)
        if txn is not None:
            registration.transaction = txn

    def _migrate_registration_statuses(self, old_reg, registration):
        for old_status in getattr(old_reg, '_statuses', {}).itervalues():
            try:
                info = self.status_map[old_status._status]
            except KeyError:
                if old_status._value:
                    val = convert_to_unicode(old_status._value._caption) if old_status._value else None
                    self.importer.print_warning(cformat('Skipping deleted status %{red!}{}%{reset} ({})')
                                                .format(convert_to_unicode(old_status._status._caption), val),
                                                event_id=self.event.id)
                continue
            field = info['field']
            status_info = info['choices'][old_status._value] if old_status._value else None
            data = {status_info['uuid']: 1} if status_info is not None else None
            registration.data.append(RegistrationData(field_data=field.current_data, data=data))
            if not self.importer.quiet and status_info:
                self.importer.print_info(cformat('%{red}STATUS%{reset} %{yellow!}{}%{reset} %{cyan}{}')
                                         .format(field.title, status_info['caption']))

    def _migrate_registration_sessions(self, old_reg, registration):
        if not old_reg._sessions:
            return
        elif self.multi_session_field:
            self._migrate_registration_sessions_multi(old_reg, registration)
        elif self.specific_session_fields:
            self._migrate_registration_sessions_specific(old_reg, registration)
        else:
            raise RuntimeError('{} has sessions but the new form has no session fields'.format(old_reg))

    def _migrate_registration_sessions_multi(self, old_reg, registration):
        old_sessions = old_reg._sessions
        choice_map, data_version = self._get_session_objects(old_sessions)
        choices = {choice_map[old_sess._regSession]: 1 for old_sess in old_sessions}
        registration.data.append(RegistrationData(field_data=data_version, data=choices))
        if not self.importer.quiet:
            self.importer.print_info(cformat('%{blue!}SESSIONS%{reset} %{cyan!}{}')
                                     .format(', '.join(_sanitize(old_sess._regSession._session.title)
                                                       for old_sess in old_sessions)))

    def _migrate_registration_sessions_specific(self, old_reg, registration):
        old_sessions = old_reg._sessions
        choice_map, data_versions = self._get_session_objects(old_sessions[:2])
        for i, old_sess in enumerate(old_sessions[:2]):
            uuid = choice_map[old_sess._regSession]
            registration.data.append(RegistrationData(field_data=data_versions[i], data={uuid: 1}))
            if not self.importer.quiet:
                self.importer.print_info(cformat('%{blue!}SESSION/{}%{reset} %{cyan!}{}')
                                         .format(i + 1, _sanitize(old_sess._regSession._session.title)))

    def _get_session_objects(self, old_sessions):
        # everything exists in the current version
        if all(old_sess._regSession in self.session_choice_map for old_sess in old_sessions):
            if self.specific_session_fields:
                return self.session_choice_map, (self.specific_session_fields[0].current_data,
                                                 self.specific_session_fields[1].current_data)
            else:
                return self.session_choice_map, self.multi_session_field.current_data

        if self.session_extra_choice_versions is None:
            # create one version that covers all choices not available in the current version
            self.importer.print_info(cformat('%{magenta!}{}').format('Creating version for missing sessions'))
            self.session_extra_choice_map = dict(self.session_choice_map)
            choices = list(self.session_choices)
            done = set(self.session_choice_map.viewkeys())
            captions = {}
            for old_reg in self.event._registrants.itervalues():
                for old_sess in old_reg._sessions:
                    old_reg_sess = old_sess._regSession
                    if old_reg_sess in done:
                        continue
                    uuid = unicode(uuid4())
                    data = {'id': uuid, 'price': 0, 'is_billable': False, 'is_enabled': True,
                            'caption': _sanitize(old_reg_sess._session.title)}
                    if self.multi_session_field:
                        # we don't create separate versions based on the prices since luckily there are
                        # no billable sessions!  and in any case, those would be handled fine by the
                        # registration-level `price_adjustment`
                        data['is_billable'], data['price'] = self._convert_billable(old_reg_sess)
                    choices.append(data)
                    captions[uuid] = data['caption']
                    self.session_extra_choice_map[old_reg_sess] = uuid
                    done.add(old_reg_sess)
            if self.specific_session_fields:
                versioned_data = [None] * 2
                for i in xrange(2):
                    self.specific_session_fields[i].data['captions'].update(captions)
                    versioned_data[i] = deepcopy(self.specific_session_fields[i].current_data.versioned_data)
                    versioned_data[i]['choices'] = choices
                    flag_modified(self.specific_session_fields[i], 'data')
                self.session_extra_choice_versions = (
                    RegistrationFormFieldData(field=self.specific_session_fields[0], versioned_data=versioned_data[0]),
                    RegistrationFormFieldData(field=self.specific_session_fields[1], versioned_data=versioned_data[1])
                )
            else:
                self.multi_session_field.data['captions'].update(captions)
                flag_modified(self.multi_session_field, 'data')
                versioned_data = deepcopy(self.multi_session_field.current_data.versioned_data)
                versioned_data['choices'] = choices
                self.session_extra_choice_versions = (
                    RegistrationFormFieldData(field=self.multi_session_field, versioned_data=versioned_data),
                )

        if self.specific_session_fields:
            return self.session_extra_choice_map, self.session_extra_choice_versions
        else:
            return self.session_extra_choice_map, self.session_extra_choice_versions[0]

    def _migrate_registration_reason(self, old_reg, registration):
        if not old_reg._reasonParticipation:
            return
        reason = convert_to_unicode(old_reg._reasonParticipation).strip()
        if not reason:
            return
        if not self.importer.quiet:
            self.importer.print_info(cformat('%{blue!}REASON%{reset} %{yellow!}{}%{reset} %{cyan!}{}')
                                     .format(self.reason_field.title, reason))
        registration.data.append(RegistrationData(field_data=self.reason_field.current_data,
                                                  data=reason))

    def _migrate_registration_social_events(self, old_reg, registration):
        if not old_reg._socialEvents:
            return
        field = self.social_events_field
        old_events = old_reg._socialEvents
        simple = True
        key = set()
        for se in old_events:
            billable, price = self._convert_billable(se)
            price_per_place = getattr(se, '_pricePerPlace', False)
            if self.social_events_info_map.get(se._socialEventItem) != (billable, price, price_per_place):
                simple = False
            key.add((se._socialEventItem, billable, price, price_per_place))
        key = frozenset(key)
        if simple:
            # we can use the current data version
            data = {self.social_events_choice_map[se._socialEventItem]: int(se._noPlaces)
                    for se in old_events}
            registration.data.append(RegistrationData(field_data=field.current_data, data=data))
        elif key in self.social_events_versions:
            # we can reuse a custom version
            info = self.social_events_versions[key]
            data = {info['mapping'][se._socialEventItem]: int(se._noPlaces) for se in old_events}
            registration.data.append(RegistrationData(field_data=info['data_version'], data=data))
        else:
            # we have to use a custom version
            data = {}
            mapping = {}
            data_version = RegistrationFormFieldData(field=field)
            data_version.versioned_data = deepcopy(field.current_data.versioned_data)
            for se in old_events:
                uuid = unicode(uuid4())
                assert uuid not in field.data['captions']
                field.data['captions'][uuid] = _sanitize(se._socialEventItem._caption)
                billable, price = self._convert_billable(se)
                data_version.versioned_data['choices'].append({
                    'id': uuid,
                    'extra_slots_pay': bool(getattr(se, '_pricePerPlace', False)),
                    'max_extra_slots': int(getattr(se._socialEventItem, '_maxPlacePerRegistrant', 0)),
                    'price': price,
                    'is_billable': billable,
                    'is_enabled': not getattr(se._socialEventItem, '_cancelled', False),
                    'places_limit': int(getattr(se._socialEventItem, '_placesLimit', 0))
                })
                mapping[se._socialEventItem] = uuid
                data[uuid] = int(se._noPlaces)
            self.social_events_versions[key] = {'data_version': data_version, 'mapping': mapping}
            registration.data.append(RegistrationData(field_data=data_version, data=data))

    def _migrate_registration_accommodation(self, old_reg, registration):
        old_ac = old_reg._accommodation
        ac_type = old_ac._accommodationType
        if ac_type is None:
            return
        field = self.accommodation_field
        billable, price = self._convert_billable(old_ac)
        data = {'arrival_date': old_ac._arrivalDate.date().strftime('%Y-%m-%d'),
                'departure_date': old_ac._departureDate.date().strftime('%Y-%m-%d')}
        if not self.importer.quiet:
            self.importer.print_info(
                cformat('%{blue!}ACCOMODATION%{reset} %{cyan!}{} [{} - {}]%{reset} %{red!}{}').format(
                    _sanitize(ac_type._caption), data['arrival_date'], data['departure_date'],
                    '{:.02f}'.format(price) if billable and price else ''))
        uuid = self.accommodation_choice_map.get(ac_type)
        if uuid is not None:
            data['choice'] = uuid
            version_with_item = None
            for version in [field.current_data] + field.data_versions:
                choice = next((x for x in version.versioned_data['choices'] if x['id'] == uuid), None)
                if choice is None:
                    continue
                version_with_item = version
                if choice['is_billable'] == billable and choice['price'] == price:
                    data_version = version
                    break
            else:
                assert version_with_item is not None
                data_version = RegistrationFormFieldData(field=field)
                data_version.versioned_data = deepcopy(version_with_item.versioned_data)
                choice = next((x for x in data_version.versioned_data['choices'] if x['id'] == uuid), None)
                choice['is_billable'] = billable
                choice['price'] = price
        else:
            uuid = unicode(uuid4())
            data['choice'] = uuid
            data_version = RegistrationFormFieldData(field=field)
            data_version.versioned_data = deepcopy(field.current_data.versioned_data)
            field.data['captions'][uuid] = _sanitize(ac_type._caption)
            data_version.versioned_data['choices'].append({
                'price': price,
                'is_billable': billable,
                'places_limit': int(getattr(ac_type, '_placesLimit', 0)),
                'is_enabled': not getattr(ac_type, '_cancelled', False),
                'caption': _sanitize(ac_type._caption),
                'id': uuid
            })
        registration.data.append(RegistrationData(field_data=data_version, data=data))

    def _migrate_registration_fields(self, old_reg, registration):
        for mig in old_reg._miscellaneous.itervalues():
            for item_id, item in mig._responseItems.iteritems():
                if get_input_type_id(item._generalField._input) == 'label':
                    billable, price = self._convert_billable(item)
                    if billable and price:
                        registration.base_price += Decimal(price)
                        if not self.importer.quiet:
                            self.importer.print_info(
                                cformat('%{blue!}STATIC%{reset} %{cyan!}{}%{reset} %{red!}{}').format(
                                    _sanitize(item._generalField._caption),
                                    '{:.02f}'.format(price) if billable and price else ''))
                elif item._generalField._id != item_id:
                    self.importer.print_warning('Skipping invalid data (field id mismatch) for obsolete version of '
                                                '"{}" (registrant {})'
                                                .format(_sanitize(item._generalField._caption), old_reg._id),
                                                event_id=self.event.id)
                else:
                    self._migrate_registration_field(item, registration)

    def _migrate_registration_field(self, old_item, registration):
        try:
            field = self.field_map[old_item._generalField]
        except KeyError:
            field = self._migrate_deleted_field(old_item._generalField)
        data_version = field.current_data
        billable, price = self._convert_billable(old_item)
        if not self.importer.quiet:
            self.importer.print_info(cformat('%{yellow!}{}%{reset} %{cyan!}{}%{reset} %{red!}{}')
                                     .format(_sanitize(old_item._generalField._caption),
                                             _sanitize(str(old_item._value)),
                                             '{:.02f}'.format(price) if billable and price else ''))
        attrs = {}
        if field.input_type in {'text', 'textarea', 'email'}:
            if isinstance(old_item._value, basestring):
                attrs['data'] = convert_to_unicode(old_item._value)
            else:
                self.importer.print_warning(cformat("Non-string '%{red}{!r}%{reset}' in {} field")
                                            .format(old_item._value, field.input_type), event_id=self.event.id)
                attrs['data'] = unicode(old_item._value)
        elif field.input_type == 'number':
            if not isinstance(old_item._value, (int, float)) and not old_item._value:
                return
            try:
                attrs['data'] = float(old_item._value)
            except ValueError:
                self.importer.print_warning(cformat("Garbage number '%{red}{0}%{reset}' in number field")
                                            .format(old_item._value), event_id=self.event.id)
            else:
                if attrs['data'] == int(attrs['data']):
                    # if we store a float we keep an ugly '.0'
                    attrs['data'] = int(attrs['data'])
            data_version = self._ensure_version_price(field, billable, price) or data_version
        elif field.input_type == 'phone':
            attrs['data'] = normalize_phone_number(convert_to_unicode(old_item._value))
        elif field.input_type == 'date':
            if old_item._value:
                dt = (datetime.strptime(old_item._value, field.data['date_format'])
                      if isinstance(old_item._value, basestring)
                      else old_item._value)
                attrs['data'] = dt.isoformat()
        elif field.input_type in {'bool', 'checkbox'}:
            attrs['data'] = old_item._value == 'yes'
            data_version = self._ensure_version_price(field, billable, price) or data_version
        elif field.input_type == 'country':
            attrs['data'] = old_item._value
        elif field.input_type == 'file':
            if not old_item._value:
                return
            local_file = old_item._value
            content_type = mimetypes.guess_type(local_file.fileName)[0] or 'application/octet-stream'
            storage_backend, storage_path, size = self.importer._get_local_file_info(local_file)
            filename = secure_filename(local_file.fileName, 'attachment')
            if storage_path is None:
                self.importer.print_error(cformat('%{red!}File not found on disk; skipping it [{}]')
                                          .format(local_file.id), event_id=self.event.id)
                return
            attrs['filename'] = filename
            attrs['content_type'] = content_type
            attrs['storage_backend'] = storage_backend
            attrs['storage_file_id'] = storage_path
            attrs['size'] = size

        elif field.input_type == 'single_choice':
            try:
                value = _sanitize(old_item._value)
            except RuntimeError:
                self.importer.print_warning(cformat("Garbage caption '%{red}{!r}%{reset}' in choice field")
                                            .format(old_item._value), event_id=self.event.id)
                return
            rv = self._migrate_registration_choice_field(field, value, price, billable)
            if rv is None:
                return
            attrs['data'] = rv['data']
            data_version = rv.get('data_version', data_version)
        else:
            raise ValueError('Unexpected field type: ' + field.input_type)
        registration.data.append(RegistrationData(field_data=data_version, **attrs))

    def _ensure_version_price(self, field, billable, price):
        if field.versioned_data['is_billable'] == billable and field.versioned_data['price'] == price:
            return None
        try:
            return self.price_adjusted_versions[(field, billable, price)]
        except KeyError:
            data_version = RegistrationFormFieldData(field=field)
            data_version.versioned_data = deepcopy(field.current_data.versioned_data)
            data_version.versioned_data['is_billable'] = billable
            data_version.versioned_data['price'] = price
            self.price_adjusted_versions[(field, billable, price)] = data_version
            return data_version

    def _migrate_registration_choice_field(self, field, selected, price, billable):
        rv = {}
        uuid = next((id_ for id_, caption in field.data['captions'].iteritems() if caption == selected), None)
        if uuid is not None:
            rv['data'] = {uuid: 1}
            version_with_item = None
            for data_version in [field.current_data] + field.data_versions:
                choice = next((x for x in data_version.versioned_data['choices'] if x['id'] == uuid), None)
                if choice is None:
                    continue
                version_with_item = data_version
                if choice['is_billable'] == billable and choice['price'] == price:
                    rv['data_version'] = data_version
                    break
            else:
                assert version_with_item is not None
                rv['data_version'] = data_version = RegistrationFormFieldData(field=field)
                data_version.versioned_data = deepcopy(version_with_item.versioned_data)
                choice = next((x for x in data_version.versioned_data['choices'] if x['id'] == uuid), None)
                choice['is_billable'] = billable
                choice['price'] = price
        elif not selected:
            return
        else:
            uuid = unicode(uuid4())
            rv['data'] = {uuid: 1}
            rv['data_version'] = data_version = RegistrationFormFieldData(field=field)
            data_version.versioned_data = deepcopy(field.current_data.versioned_data)
            field.data['captions'][uuid] = selected
            data_version.versioned_data['choices'].append({
                'price': price,
                'is_billable': billable,
                'places_limit': 0,
                'is_enabled': True,
                'caption': selected,
                'id': uuid
            })
        return rv


class EventRegformImporter(LocalFileImporterMixin, Importer):
    def __init__(self, **kwargs):
        kwargs = self._set_config_options(**kwargs)
        super(EventRegformImporter, self).__init__(**kwargs)

    def has_data(self):
        return RegistrationForm.find(RegistrationForm.title != 'Participants').has_rows()

    def load_data(self):
        self.print_step("Loading some data")
        self.all_users_by_email = {}
        for user in User.query.options(joinedload('_all_emails')):
            if user.is_deleted:
                continue
            for email in user.all_emails:
                self.all_users_by_email[email] = user
        self.all_payment_settings = defaultdict(dict)
        setting_names = ['register_email', 'success_email', 'enabled']
        for setting in EventSetting.find(EventSetting.module == 'payment', EventSetting.name.in_(setting_names)):
            if setting.value:
                value = setting.value.strip() if isinstance(setting.value, basestring) else setting.value
                if value:
                    self.all_payment_settings[setting.event_id][setting.name] = value
        self.participant_list_disabled = {x for x, in db.session.query(MenuEntry.event_id)
                                                                .filter(MenuEntry.name == 'participants',
                                                                        ~MenuEntry.is_enabled)}

    @contextmanager
    def _monkeypatch(self):
        old = Conference.getType

        def _get_type(conf):
            wf = self.zodb_root['webfactoryregistry'].get(conf.id)
            return 'conference' if wf is None else wf.getId()

        Conference.getType = _get_type
        try:
            yield
        finally:
            Conference.getType = old

    def migrate(self):
        self.load_data()
        self.migrate_regforms()
        with self._monkeypatch():
            self.enable_features()
        self.sync_friendly_ids()
        self.update_merged_users(Registration.user, "registrations")

    def migrate_regforms(self):
        self.print_step("Migrating registration forms")
        for event, regform in committing_iterator(self._iter_regforms(), 10):
            mig = RegformMigration(self, event, regform)
            with db.session.no_autoflush:
                mig.run()
            db.session.add(mig.regform)
            db.session.flush()

    def sync_friendly_ids(self):
        self.print_step("Synchronizing friendly IDs")
        value = db.func.coalesce(db.session.query(db.func.max(Registration.friendly_id)).
                                 filter(Registration.event_id == Event.id)
                                 .as_scalar(), 0)
        Event.query.update({Event._last_friendly_registration_id: value}, synchronize_session=False)

    def enable_features(self):
        self.print_step("Enabling payment/registration features")
        event_ids = [x[0] for x in set(db.session.query(RegistrationForm.event_id))]
        it = verbose_iterator(event_ids, len(event_ids), lambda x: x,
                              lambda x: self.zodb_root['conferences'][str(x)].title)
        for event_id in committing_iterator(it):
            set_feature_enabled(self.zodb_root['conferences'][str(event_id)], 'registration', True)
            if self.all_payment_settings.get(event_id, {}).get('enabled'):
                set_feature_enabled(self.zodb_root['conferences'][str(event_id)], 'payment', True)

    def _iter_regforms(self):
        it = self.zodb_root['conferences'].itervalues()
        if self.quiet:
            it = verbose_iterator(it, len(self.zodb_root['conferences']), attrgetter('id'), attrgetter('title'))

        for event in self.flushing_iterator(it):
            try:
                regform = event._registrationForm
            except AttributeError:
                self.print_warning('Event has no regform', event_id=event.id)
                continue
            else:
                if (not event._registrants and
                        (not regform.activated or
                         regform.startRegistrationDate.date() == regform.endRegistrationDate.date())):
                    # no registrants and not enabled or enabled but most likely unconfigured (same start/end date)
                    continue
            yield event, regform

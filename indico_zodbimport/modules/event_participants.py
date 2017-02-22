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
from contextlib import contextmanager
from itertools import chain
from HTMLParser import HTMLParser
from operator import attrgetter
from uuid import uuid4

from sqlalchemy.orm import joinedload
from werkzeug.utils import cached_property

from indico.core.db import db
from indico.modules.events.features.util import set_feature_enabled
from indico.modules.events.registration.models.form_fields import RegistrationFormField
from indico.modules.events.registration.models.forms import RegistrationForm, ModificationMode
from indico.modules.events.registration.models.items import RegistrationFormSection, PersonalDataType
from indico.modules.events.registration.models.registrations import Registration, RegistrationState, RegistrationData
from indico.modules.events.registration.util import create_personal_data_fields
from indico.modules.users import User
from indico.util.caching import memoize
from indico.util.console import verbose_iterator, cformat
from indico.util.date_time import now_utc
from indico.util.string import normalize_phone_number
from indico.util.struct.iterables import committing_iterator
from indico.web.flask.templating import strip_tags

from indico_zodbimport import Importer, convert_to_unicode


WHITESPACE_RE = re.compile(r'\s+')
PARTICIPATION_FORM_TITLE = 'Participants'

PARTICIPANT_ATTR_MAP = {
    PersonalDataType.affiliation: '_affiliation',
    PersonalDataType.address: '_address',
    PersonalDataType.phone: '_telephone'
}

PARTICIPANT_STATUS_MAP = {
    'declined': RegistrationState.rejected,
    'refused': RegistrationState.withdrawn,
    'rejected': RegistrationState.withdrawn,
    'pending': RegistrationState.pending
}


@memoize
def _sanitize(string, html=False):
    string = convert_to_unicode(string)
    if not html:
        string = HTMLParser().unescape(strip_tags(string))
    return WHITESPACE_RE.sub(' ', string).strip()


class ParticipationMigration(object):
    def __init__(self, importer, event, old_participation):
        self.importer = importer
        self.event = event
        self.old_participation = old_participation
        self.regform = None
        self.emails = set()
        self.users = set()
        self.pd_field_map = {}
        self.status_field = None
        self.status_map = {}
        self.title_map = {}
        self.past_event = self.event.endDate < now_utc()

    def __repr__(self):
        return 'ParticipationMigration({})'.format(self.event)

    def run(self):
        self.regform = RegistrationForm(event_id=int(self.event.id), title=PARTICIPATION_FORM_TITLE,
                                        is_participation=True)
        if not self.importer.quiet:
            self.importer.print_success(cformat('%{cyan}{}').format(self.regform.title), event_id=self.event.id)
        self._migrate_settings()
        self._create_form()
        self._migrate_participants()

    def iter_participants(self):
        return chain(self.old_participation._participantList.itervalues(),
                     self.old_participation._pendingParticipantList.itervalues(),
                     getattr(self.old_participation, '_declinedParticipantList', {}).itervalues())

    @cached_property
    def status_used(self):
        default_statuses = {'added', 'pending'}
        return any(p._status not in default_statuses for p in self.iter_participants())

    def _migrate_settings(self):
        old_part = self.old_participation
        if old_part._allowedForApplying:
            self.regform.start_dt = self.event._creationDS
            self.regform.end_dt = self.event.endDate
        self.regform.moderation_enabled = not getattr(old_part, '_autoAccept', False)
        self.regform.publish_registrations_enabled = old_part._displayParticipantList
        self.regform.registration_limit = max(0, int(getattr(old_part, '_numMaxParticipants', 0))) or None
        self.regform.manager_notifications_enabled = getattr(old_part, '_notifyMgrNewParticipant', False)
        self.regform.modification_mode = ModificationMode.not_allowed
        # manager emails are migrated afterwards

    def _create_form(self):
        create_personal_data_fields(self.regform)
        for item in self.regform.form_items:
            if not item.is_field:
                item.position = 1  # pd section
                continue
            # we have nothing but personal data fields right now. no need for extra checks!
            if item.personal_data_type != PersonalDataType.country:
                self.pd_field_map[item.personal_data_type] = item
            if item.personal_data_type == PersonalDataType.title:
                self.title_map = {v: k for k, v in item.data['captions'].iteritems()}

        # create administrative section for statuses
        if self.status_used:
            section = RegistrationFormSection(registration_form=self.regform, is_manager_only=True, title='Status',
                                              position=2)
            if self.status_used:
                choices = []
                for status in ('refused', 'excused', 'invited', 'accepted', 'rejected', 'declined'):
                    uuid = unicode(uuid4())
                    caption = status.title()
                    choices.append({'price': 0, 'is_billable': False, 'places_limit': 0, 'is_enabled': True,
                                    'caption': caption, 'id': uuid})
                    self.status_map[status] = {'uuid': uuid, 'caption': caption}
                field_data = {
                    'item_type': 'dropdown',
                    'with_extra_slots': False,
                    'default_item': None,
                    'choices': choices
                }
                self.status_field = field = RegistrationFormField(registration_form=self.regform, parent=section,
                                                                  input_type='single_choice', title='Status')
                field.data, field.versioned_data = field.field_impl.process_field_data(field_data)

    def _migrate_participants(self):
        for old_part in self.iter_participants():
            self.regform.registrations.append(self._migrate_participant(old_part))

    def _migrate_participant(self, old_part):
        state = PARTICIPANT_STATUS_MAP.get(old_part._status, RegistrationState.complete)
        registration = Registration(first_name=convert_to_unicode(old_part._firstName),
                                    last_name=convert_to_unicode(old_part._familyName),
                                    email=self._fix_email(old_part._email),
                                    submitted_dt=self.event._creationDS,
                                    base_price=0, price_adjustment=0,
                                    checked_in=old_part._present, state=state)
        self.importer.print_info(cformat('%{yellow}Registration%{reset} - %{cyan}{}%{reset} [{}]')
                                 .format(registration.full_name, state.title))
        self._migrate_participant_user(old_part, registration)
        self._migrate_participant_data(old_part, registration)
        self._migrate_participant_status(old_part, registration)
        return registration

    def _fix_email(self, email):
        email = convert_to_unicode(email).lower() or 'no-email@example.com'
        no_email = email == 'no-email@example.com'
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
        if n != 1 and not no_email:
            self.importer.print_warning(cformat('Duplicate email %{yellow}{}@{}%{reset}; using %{green}{}%{reset} '
                                                'instead').format(user, host, email),
                                        event_id=self.event.id)
        self.emails.add(email)
        return email

    def _migrate_participant_user(self, old_part, registration):
        user = self.importer.all_users_by_email.get(registration.email)
        if user is not None:
            if user in self.users:
                self.importer.print_warning(cformat('User {} is already associated with a registration; not '
                                                    'associating them with {}').format(user, registration),
                                            event_id=self.event.id)
                return
            self.users.add(user)
            registration.user = user
        if not self.past_event and old_part._avatar and old_part._avatar.user:
            if not registration.user:
                self.importer.print_warning(cformat('No email match; discarding association between {} and {}')
                                            .format(old_part._avatar.user, registration), event_id=self.event.id)
            elif registration.user != old_part._avatar.user:
                self.importer.print_warning(cformat('Email matches other user; associating {} with {} instead of {}')
                                            .format(registration, registration.user, old_part._avatar.user),
                                            event_id=self.event.id)

    def _migrate_participant_data(self, old_part, registration):
        for pd_type, field in self.pd_field_map.iteritems():
            if pd_type.column:
                friendly_value = value = getattr(registration, pd_type.column)
            elif pd_type == PersonalDataType.title:
                try:
                    value = {self.title_map[old_part._title]: 1}
                except KeyError:
                    value = None
                friendly_value = convert_to_unicode(old_part._title)
            elif pd_type == PersonalDataType.position:
                continue
            else:
                value = convert_to_unicode(getattr(old_part, PARTICIPANT_ATTR_MAP[pd_type]))
                if pd_type == PersonalDataType.phone and value:
                    value = normalize_phone_number(value)
                friendly_value = value
            if value:
                field.is_enabled = True
            if not self.importer.quiet:
                self.importer.print_info(cformat('%{yellow!}{}%{reset} %{cyan!}{}%{reset}')
                                         .format(pd_type.name, friendly_value))
            registration.data.append(RegistrationData(field_data=field.current_data, data=value))

    def _migrate_participant_status(self, old_part, registration):
        if not self.status_used:
            return
        if old_part._status not in {'added', 'pending'}:
            status_info = self.status_map[old_part._status]
            data = {status_info['uuid']: 1}
            caption = status_info['caption']
        else:
            data = None
            caption = ''
        if not self.importer.quiet and data:
            self.importer.print_info(cformat('%{red}STATUS%{reset} %{cyan}{}').format(caption))
        registration.data.append(RegistrationData(field_data=self.status_field.current_data, data=data))


class EventParticipantsImporter(Importer):
    def has_data(self):
        return RegistrationForm.find(title=PARTICIPATION_FORM_TITLE).has_rows()

    def load_data(self):
        self.print_step("Loading some data")
        self.all_users_by_email = {}
        for user in User.query.options(joinedload('_all_emails')):
            if user.is_deleted:
                continue
            for email in user.all_emails:
                self.all_users_by_email[email] = user

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
        self.set_manager_emails()
        with self._monkeypatch():
            self.enable_features()
        self.update_merged_users(Registration.user, "registrations")

    def migrate_regforms(self):
        self.print_step("Migrating participants")
        for event, participation in committing_iterator(self._iter_participations(), 10):
            mig = ParticipationMigration(self, event, participation)
            with db.session.no_autoflush:
                mig.run()
            db.session.add(mig.regform)
            db.session.flush()

    def set_manager_emails(self):
        db.session.execute(db.text("""
            UPDATE event_registration.forms rf SET manager_notification_recipients = (
                SELECT array_agg(ue.email)
                FROM events.principals p
                JOIN users.emails ue ON (ue.user_id = p.user_id AND NOT ue.is_user_deleted AND ue.is_primary)
                WHERE p.event_id = rf.event_id AND p.full_access AND p.type = 1
            )
            WHERE manager_notification_recipients = '{}' AND manager_notifications_enabled AND title = :title;
        """).bindparams(title=PARTICIPATION_FORM_TITLE))
        db.session.commit()

    def enable_features(self):
        self.print_step("Enabling registration features")
        event_ids = [x[0] for x in set(db.session.query(RegistrationForm.event_id)
                                       .filter(RegistrationForm.title == PARTICIPATION_FORM_TITLE))]
        it = verbose_iterator(event_ids, len(event_ids), lambda x: x,
                              lambda x: self.zodb_root['conferences'][str(x)].title)
        for event_id in committing_iterator(it):
            set_feature_enabled(self.zodb_root['conferences'][str(event_id)], 'registration', True)

    def _iter_participations(self):
        it = self.zodb_root['conferences'].itervalues()
        if self.quiet:
            it = verbose_iterator(it, len(self.zodb_root['conferences']), attrgetter('id'), attrgetter('title'))

        for event in self.flushing_iterator(it):
            try:
                participation = event._participation
            except AttributeError:
                self.print_warning('Event has no participation', event_id=event.id)
                continue
            if participation._participantList or participation._pendingParticipantList:
                yield event, participation

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


from __future__ import unicode_literals, division

import traceback
from math import ceil
from operator import attrgetter
from uuid import uuid4

import click
from sqlalchemy.orm import joinedload, undefer

from indico.core.db import db
from indico.core.db.sqlalchemy.colors import ColorTuple
from indico.core.db.sqlalchemy.principals import EmailPrincipal
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.fields import ContributionField, ContributionFieldValue
from indico.modules.events.contributions.models.legacy_mapping import LegacyContributionMapping
from indico.modules.events.contributions.models.principals import ContributionPrincipal
from indico.modules.events.contributions.models.persons import (ContributionPersonLink, SubContributionPersonLink,
                                                                AuthorType)
from indico.modules.events.contributions.models.references import ContributionReference, SubContributionReference
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.contributions.models.types import ContributionType
from indico.modules.events.models.events import Event
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.models.references import ReferenceType, EventReference
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.legacy_mapping import LegacySessionMapping
from indico.modules.events.sessions.models.persons import SessionBlockPersonLink
from indico.modules.events.sessions.models.principals import SessionPrincipal
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.timetable.models.breaks import Break
from indico.modules.events.timetable.models.entries import TimetableEntry
from indico.modules.users import User
from indico.modules.users.models.users import UserTitle
from indico.util.console import cformat, verbose_iterator
from indico.util.string import fix_broken_string, sanitize_email, is_valid_mail
from indico.util.struct.iterables import committing_iterator
from MaKaC.conference import _get_room_mapping

from indico_zodbimport import Importer, convert_to_unicode
from indico_zodbimport.util import convert_principal, patch_default_group_provider


PROTECTION_MODE_MAP = {
    -1: ProtectionMode.public,
    0: ProtectionMode.inheriting,
    1: ProtectionMode.protected,
}

USER_TITLE_MAP = {x.title: x for x in UserTitle}

PERSON_INFO_MAP = {
    '_address': 'address',
    '_affiliation': 'affiliation',
    '_firstName': 'first_name',
    '_surName': 'last_name',
    '_phone': 'phone'
}


class TimetableMigration(object):
    def __init__(self, importer, old_event, event):
        self.importer = importer
        self.old_event = old_event
        self.event = event
        self.legacy_person_map = {}
        self.legacy_session_map = {}
        self.legacy_contribution_map = {}
        self.legacy_contribution_type_map = {}
        self.legacy_contribution_field_map = {}

    def __repr__(self):
        return '<TimetableMigration({})>'.format(self.event)

    def run(self):
        self.importer.print_success('Importing {}'.format(self.old_event), event_id=self.event.id)
        self.event.references = list(self._process_references(EventReference, self.old_event))
        self._migrate_contribution_types()
        self._migrate_sessions()
        self._migrate_contributions()
        self._migrate_timetable()

    def _convert_principal(self, old_principal):
        principal = convert_principal(old_principal)
        if (principal is None and old_principal.__class__.__name__ in ('Avatar', 'AvatarUserWrapper') and
                'email' in old_principal.__dict__):
            email = old_principal.__dict__['email'].lower()
            principal = self.importer.all_users_by_email.get(email)
            if principal is not None:
                self.importer.print_warning('Using {} for {} (matched via {})'.format(principal, old_principal, email),
                                            always=False, event_id=self.event.id)
        return principal

    def _process_principal(self, principal_cls, principals, legacy_principal, name, read_access=None, full_access=None,
                           roles=None, allow_emails=True):
        if legacy_principal is None:
            return
        elif isinstance(legacy_principal, basestring):
            user = self.importer.all_users_by_email.get(legacy_principal)
            principal = user or EmailPrincipal(legacy_principal)
        else:
            principal = self._convert_principal(legacy_principal)
        if principal is None:
            self.importer.print_warning(cformat('%{yellow}{} does not exist:%{reset} {}')
                                        .format(name, legacy_principal), always=False, event_id=self.event.id)
            return
        elif not allow_emails and isinstance(principal, EmailPrincipal):
            self.importer.print_warning(cformat('%{yellow}{} cannot be an email principal:%{reset} {}')
                                        .format(name, legacy_principal), always=False, event_id=self.event.id)
            return
        try:
            entry = principals[principal]
        except KeyError:
            entry = principal_cls(principal=principal, full_access=False, roles=[])
            principals[principal] = entry
        if read_access:
            entry.read_access = True
        if full_access:
            entry.full_access = True
        if roles:
            entry.roles = sorted(set(entry.roles) | set(roles))
        if not self.importer.quiet:
            self.importer.print_info(' - [{}] {}'.format(name.lower(), principal))

    def _process_principal_emails(self, principal_cls, principals, emails, name, read_access=None, full_access=None,
                                  roles=None, allow_emails=True):
        emails = {sanitize_email(convert_to_unicode(email).lower()) for email in emails}
        emails = {email for email in emails if is_valid_mail(email, False)}
        for email in emails:
            self._process_principal(principal_cls, principals, email, name, read_access, full_access, roles,
                                    allow_emails=allow_emails)

    def _process_ac(self, principal_cls, principals, ac, allow_emails=True):
        # read access
        for principal in ac.allowed:
            self._process_principal(principal_cls, principals, principal, 'Access', read_access=True,
                                    allow_emails=allow_emails)
        # email-based read access
        emails = getattr(ac, 'allowedEmail', [])
        self._process_principal_emails(principal_cls, principals, emails, 'Access', read_access=True,
                                       allow_emails=allow_emails)
        # managers
        for manager in ac.managers:
            self._process_principal(principal_cls, principals, manager, 'Manager', full_access=True,
                                    allow_emails=allow_emails)
        # email-based managers
        emails = getattr(ac, 'managersEmail', [])
        self._process_principal_emails(principal_cls, principals, emails, 'Manager', full_access=True,
                                       allow_emails=allow_emails)

    def _process_references(self, reference_cls, old_object):
        try:
            rnh = old_object._reportNumberHolder
        except AttributeError:
            return
        for name, values in rnh._reports.iteritems():
            try:
                reference_type = self.importer.reference_type_map[name]
            except KeyError:
                self.importer.print_warning(cformat('%{yellow!}Unknown reference type: {}').format(name),
                                            event_id=self.event.id)
                continue
            for value in map(convert_to_unicode, values):
                if not self.importer.quiet:
                    self.importer.print_info(cformat(' - %{magenta}{}: %{green!}{}').format(name, value))
                yield reference_cls(reference_type=reference_type, value=value)

    def _process_keywords(self, keywords):
        return map(convert_to_unicode, keywords.splitlines())

    def _migrate_contribution_types(self):
        for old_ct in self.old_event._contribTypes.itervalues():
            ct = ContributionType(name=convert_to_unicode(old_ct._name),
                                  description=convert_to_unicode(old_ct._description))
            if not self.importer.quiet:
                self.importer.print_info(cformat('%{cyan}Contribution type%{reset} {}').format(ct.name))
            self.legacy_contribution_type_map[old_ct] = ct
            self.event.contribution_types.append(ct)

    def _migrate_sessions(self):
        sessions = []
        friendly_id_map = {}
        friendly_ids_used = set()
        skipped = []
        for id_, session in sorted(self.old_event.sessions.items(),
                                   key=lambda x: (x[0].isdigit(), int(x[0]) if x[0].isdigit() else x[0])):
            id_ = int(id_.lstrip('s'))  # legacy: s123
            if id_ in friendly_ids_used:
                skipped.append(session)
                continue
            friendly_id_map[session] = id_
            friendly_ids_used.add(id_)
        for i, session in enumerate(skipped, (max(friendly_ids_used) if friendly_ids_used else 0) + 1):
            assert i not in friendly_ids_used
            friendly_id_map[session] = i
            friendly_ids_used.add(i)
        for old_session in self.old_event.sessions.itervalues():
            sessions.append(self._migrate_session(old_session, friendly_id_map[old_session]))
        if sessions:
            self.event._last_friendly_session_id = max(s.friendly_id for s in sessions)

    def _migrate_session(self, old_session, friendly_id=None):
        ac = old_session._Session__ac
        code = convert_to_unicode(old_session._code)
        if code == 'no code':
            code = ''
        session = Session(event_new=self.event, title=convert_to_unicode(old_session.title),
                          description=convert_to_unicode(old_session.description),
                          is_poster=(old_session._ttType == 'poster'), code=code,
                          default_contribution_duration=old_session._contributionDuration,
                          protection_mode=PROTECTION_MODE_MAP[ac._accessProtection])
        if friendly_id is not None:
            session.friendly_id = friendly_id
        else:
            # migrating a zombie session; we simply give it a new friendly id
            self.event._last_friendly_session_id += 1
            session.friendly_id = self.event._last_friendly_session_id
        if not self.importer.quiet:
            self.importer.print_info(cformat('%{blue!}Session%{reset} {}').format(session.title))
        self.legacy_session_map[old_session] = session
        session.legacy_mapping = LegacySessionMapping(event_new=self.event, legacy_session_id=old_session.id)
        # colors
        try:
            session.colors = ColorTuple(old_session._textColor, old_session._color)
        except (AttributeError, ValueError) as e:
            self.importer.print_warning(cformat('%{yellow}Session has no colors: "{}" [{}]').format(session.title, e),
                                        event_id=self.event.id)
        principals = {}
        # managers / read access
        self._process_ac(SessionPrincipal, principals, ac, allow_emails=False)
        # coordinators
        for submitter in old_session._coordinators.itervalues():
            self._process_principal(SessionPrincipal, principals, submitter, 'Coordinator', roles={'coordinate'})
        self._process_principal_emails(SessionPrincipal, principals, getattr(old_session, '_coordinatorsEmail', []),
                                       'Coordinator', roles={'coordinate'}, allow_emails=False)
        session.acl_entries = set(principals.itervalues())
        return session

    def _migrate_contributions(self):
        contribs = []
        friendly_id_map = {}
        friendly_ids_used = set()
        skipped = []
        for id_, contrib in sorted(self.old_event.contributions.items(),
                                   key=lambda x: (not x[0].isdigit(), int(x[0]) if x[0].isdigit() else x[0])):
            try:
                id_ = int(id_)  # legacy: s1t2
            except ValueError:
                skipped.append(contrib)
                continue
            if id_ in friendly_ids_used:
                skipped.append(contrib)
                continue
            friendly_id_map[contrib] = id_
            friendly_ids_used.add(id_)
        for i, contrib in enumerate(skipped, (max(friendly_ids_used) if friendly_ids_used else 0) + 1):
            assert i not in friendly_ids_used
            friendly_id_map[contrib] = i
            friendly_ids_used.add(i)
        for old_contrib in self.old_event.contributions.itervalues():
            contribs.append(self._migrate_contribution(old_contrib, friendly_id_map[old_contrib]))
        if contribs:
            self.event._last_friendly_contribution_id = max(c.friendly_id for c in contribs)

    def _migrate_contribution(self, old_contrib, friendly_id):
        ac = old_contrib._Contribution__ac
        description = old_contrib._fields.get('content', '')
        description = convert_to_unicode(getattr(description, 'value', description))  # str or AbstractFieldContent
        contrib = Contribution(event_new=self.event, friendly_id=friendly_id,
                               title=convert_to_unicode(old_contrib.title),
                               description=description, duration=old_contrib.duration,
                               protection_mode=PROTECTION_MODE_MAP[ac._accessProtection],
                               keywords=self._process_keywords(old_contrib._keywords))
        if not self.importer.quiet:
            self.importer.print_info(cformat('%{cyan}Contribution%{reset} {}').format(contrib.title))
        self.legacy_contribution_map[old_contrib] = contrib
        contrib.legacy_mapping = LegacyContributionMapping(event_new=self.event, legacy_contribution_id=old_contrib.id)
        # contribution type
        if old_contrib._type is not None:
            try:
                contrib.type = self.legacy_contribution_type_map[old_contrib._type]
            except AttributeError:
                self.importer.print_warning(cformat('%{yellow!}Invalid contrib type {}')
                                            .format(convert_to_unicode(old_contrib._type._name)),
                                            event_id=self.event.id)
        # ACLs (managers, read access, submitters)
        principals = {}
        self._process_ac(ContributionPrincipal, principals, ac)
        for submitter in old_contrib._submitters:
            self._process_principal(ContributionPrincipal, principals, submitter, 'Submitter', roles={'submit'})
        self._process_principal_emails(ContributionPrincipal, principals, getattr(old_contrib, '_submittersEmail', []),
                                       'Submitter', roles={'submit'})
        contrib.acl_entries = set(principals.itervalues())
        # speakers, authors and co-authors
        contrib.person_links = list(self._migrate_contribution_persons(old_contrib))
        contrib.references = list(self._process_references(ContributionReference, old_contrib))
        contrib.field_values = list(self._migrate_contribution_fields(old_contrib))
        contrib.subcontributions = [self._migrate_subcontribution(old_subcontrib, pos)
                                    for pos, old_subcontrib in enumerate(old_contrib._subConts, 1)]
        contrib._last_friendly_subcontribution_id = len(contrib.subcontributions)
        return contrib

    def _migrate_contribution_fields(self, old_contrib):
        fields = dict(old_contrib._fields)
        fields.pop('content', None)
        for field_content in fields.itervalues():
            legacy_field_option_id_map = {}
            new_field = self._process_contribution_field(field_content.field, legacy_field_option_id_map)
            if not new_field:
                continue
            new_value = self._process_contribution_field_value(field_content, new_field, legacy_field_option_id_map)
            if new_value:
                yield new_value

    def _process_contribution_field(self, old_field, legacy_field_option_id_map):
        field = self.legacy_contribution_field_map.get(old_field)
        if field:
            return field
        field_type = old_field.__class__.__name__
        if field_type in ('AbstractTextAreaField', 'AbstractInputField'):
            field_data = {
                'max_length': int(old_field._maxLength) if old_field._limitation == 'chars' else None,
                'max_words': int(old_field._maxLength) if old_field._limitation == 'words' else None,
                'multiline': field_type == 'AbstractTextAreaField'
            }
            field_type = 'text'
        elif field_type == 'AbstractSelectionField':
            options = []
            for opt in old_field._options:
                uuid = unicode(uuid4())
                legacy_field_option_id_map[opt.id] = uuid
                options.append({'option': convert_to_unicode(opt.value), 'id': uuid, 'is_deleted': False})
            for deleted_opt in old_field._deleted_options:
                uuid = unicode(uuid4())
                legacy_field_option_id_map[opt.id] = uuid
                options.append({'option': convert_to_unicode(opt.value), 'id': uuid, 'is_deleted': True})
            field_data = {'options': options, 'display_type': 'select'}
            field_type = 'single_choice'
        else:
            self.importer.print_error('Unrecognized field type {}'.format(field_type), event_id=self.event.id)
            return None
        field = ContributionField(event_new=self.event, field_type=field_type, is_active=old_field._active,
                                  title=convert_to_unicode(old_field._caption), is_required=old_field._isMandatory,
                                  field_data=field_data)
        self.legacy_contribution_field_map[old_field] = field
        if not self.importer.quiet:
            self.importer.print_info(cformat('%{magenta} - [contribution_field]: {}').format(field.title))
        return field

    def _process_contribution_field_value(self, old_data, new_field, legacy_field_option_id_map):
        if not old_data.value:
            return
        field_type = old_data.field.__class__.__name__
        if field_type in ('AbstractTextAreaField', 'AbstractInputField'):
            data = convert_to_unicode(old_data.value)
            return ContributionFieldValue(contribution_field=new_field, data=data)
        elif field_type == 'AbstractSelectionField':
            data = legacy_field_option_id_map[old_data.value]
            return ContributionFieldValue(contribution_field=new_field, data=data)
        else:
            self.importer.print_error('Unrecognized field type {}. Value not imported.'.format(field_type),
                                      event_id=self.event.id)

    def _migrate_subcontribution(self, old_subcontrib, position):
        subcontrib = SubContribution(position=position, friendly_id=position, duration=old_subcontrib.duration,
                                     title=convert_to_unicode(old_subcontrib.title),
                                     description=convert_to_unicode(old_subcontrib.description))
        if not self.importer.quiet:
            self.importer.print_info(cformat('  %{cyan!}SubContribution%{reset} {}').format(subcontrib.title))
        subcontrib.references = list(self._process_references(SubContributionReference, old_subcontrib))
        subcontrib.person_links = list(self._migrate_subcontribution_persons(old_subcontrib))
        return subcontrib

    def _migrate_contribution_persons(self, old_entry):
        person_link_map = {}
        for speaker in getattr(old_entry, '_speakers', []):
            person = self._migrate_person(speaker)
            if not person:
                continue
            link = person_link_map.get(person)
            if link:
                link.is_speaker = True
            else:
                link = ContributionPersonLink(person=person, is_speaker=True)
                person_link_map[person] = link
                yield link
        for author in getattr(old_entry, '_primaryAuthors', []):
            person = self._migrate_person(author)
            if not person:
                continue
            link = person_link_map.get(person)
            if link:
                link.author_type = AuthorType.primary
            else:
                link = ContributionPersonLink(person=person, author_type=AuthorType.primary)
                person_link_map[person] = link
                yield link
        for coauthor in getattr(old_entry, '_coAuthors', []):
            person = self._migrate_person(coauthor)
            if not person:
                continue
            link = person_link_map.get(person)
            if link:
                if link.author_type == AuthorType.primary:
                    self.importer.print_warning(cformat('%{yellow}!Primary author "{}" is also co-author')
                                                .format(person.full_name), event_id=self.event.id)
                else:
                    link.author_type = AuthorType.secondary
            else:
                link = ContributionPersonLink(person=person, author_type=AuthorType.secondary)
                person_link_map[person] = link
                yield link

    def _migrate_subcontribution_persons(self, old_entry):
        person_link_map = {}
        for speaker in getattr(old_entry, 'speakers', []):
            person = self._migrate_person(speaker)
            if not person:
                continue
            link = person_link_map.get(person)
            if link:
                self.importer.print_warning(
                    cformat('%{yellow!}Duplicated speaker "{}" for sub-contribution').format(person.full_name),
                    event_id=self.event.id
                )
            else:
                link = SubContributionPersonLink(person=person)
                person_link_map[person] = link
                yield link

    def _migrate_session_block_persons(self, old_entry):
        person_link_map = {}
        for convener in getattr(old_entry, '_conveners', []):
            person = self._migrate_person(convener)
            if not person:
                continue
            link = person_link_map.get(person)
            if link:
                self.importer.print_warning(
                    cformat('%{yellow!}Duplicated session block convener "{}"').format(person.full_name),
                    event_id=self.event.id
                )
            else:
                link = SessionBlockPersonLink(person=person)
                person_link_map[person] = link
                yield link

    def _migrate_person(self, old_person):
        first_name = convert_to_unicode(getattr(old_person, '_firstName', ''))
        last_name = convert_to_unicode(getattr(old_person, '_surName', ''))
        email = convert_to_unicode(getattr(old_person, '_email', ''))
        affiliation = convert_to_unicode(getattr(old_person, '_affiliation', ''))
        if not first_name and not last_name and (email or affiliation):
            self.importer.print_warning(cformat('%{yellow!}Skipping nameless event person'), event_id=self.event.id)
            return
        key = (first_name, last_name, email, affiliation)
        existing_person = self.legacy_person_map.get(key)
        if existing_person:
            self._build_person(old_person, existing_person, key)
            return existing_person
        person = EventPerson(event_new=self.event)
        self._build_person(old_person, person, key)
        if not self.importer.quiet:
            self.importer.print_info(cformat(' %{magenta!}- [event_person]%{reset} {}').format(person.full_name))
        if person.email:
            user = self.importer.all_users_by_email.get(person.email)
            if user:
                person.user = user
        return person

    def _build_person(self, old_person, person, map_key):
        for old_attr, new_attr in PERSON_INFO_MAP.iteritems():
            if not getattr(person, new_attr, None):
                setattr(person, new_attr, convert_to_unicode(getattr(old_person, old_attr, '')))
        if not person._title:
            person.title = USER_TITLE_MAP.get(getattr(old_person, '_title', ''), UserTitle.none)
        if not person.email:
            email = getattr(old_person, '_email', '')
            email = sanitize_email(convert_to_unicode(email).lower()) if email else ''
            if is_valid_mail(email, False):
                person.email = email
            else:
                self.importer.print_warning(cformat('%{yellow!}Skipping invalid email {}').format(email),
                                            event_id=self.event.id)
        self.legacy_person_map[map_key] = person

    def _migrate_timetable(self):
        self._migrate_timetable_entries(self.old_event._Conference__schedule._entries)

    def _migrate_timetable_entries(self, old_entries, session_block=None):
        for old_entry in old_entries:
            item_type = old_entry.__class__.__name__
            if item_type == 'ContribSchEntry':
                self._migrate_contribution_timetable_entry(old_entry, session_block)
            elif item_type == 'BreakTimeSchEntry':
                self._migrate_break_timetable_entry(old_entry, session_block)
            elif item_type == 'LinkedTimeSchEntry':
                parent = old_entry._LinkedTimeSchEntry__owner
                parent_type = parent.__class__.__name__
                if parent_type == 'Contribution':
                    self.importer.print_warning(cformat('%{yellow!}Found LinkedTimeSchEntry for contribution'),
                                                event_id=self.event.id)
                    self._migrate_contribution_timetable_entry(old_entry, session_block)
                    continue
                elif parent_type != 'SessionSlot':
                    self.importer.print_error(cformat('%{red!}Found LinkedTimeSchEntry for {}').format(parent_type),
                                              event_id=self.event.id)
                    continue
                assert session_block is None
                self._migrate_block_timetable_entry(old_entry)
            else:
                raise ValueError('Unexpected item type: ' + item_type)

    def _migrate_contribution_timetable_entry(self, old_entry, session_block=None):
        old_contrib = old_entry._LinkedTimeSchEntry__owner
        contrib = self.legacy_contribution_map[old_contrib]
        contrib.timetable_entry = TimetableEntry(event_new=self.event, start_dt=old_contrib.startDate)
        self._migrate_location(old_contrib, contrib)
        if session_block:
            contrib.session = session_block.session
            contrib.session_block = session_block
            contrib.timetable_entry.parent = session_block.timetable_entry

    def _migrate_break_timetable_entry(self, old_entry, session_block=None):
        break_ = Break(title=convert_to_unicode(old_entry.title), description=convert_to_unicode(old_entry.description),
                       duration=old_entry.duration)
        try:
            break_.colors = ColorTuple(old_entry._textColor, old_entry._color)
        except (AttributeError, ValueError) as e:
            self.importer.print_warning(cformat('%{yellow}Break has no colors: "{}" [{}]').format(break_.title, e),
                                        event_id=self.event.id)
        break_.timetable_entry = TimetableEntry(event_new=self.event, start_dt=old_entry.startDate)
        self._migrate_location(old_entry, break_)
        if session_block:
            break_.timetable_entry.parent = session_block.timetable_entry

    def _migrate_block_timetable_entry(self, old_entry):
        old_block = old_entry._LinkedTimeSchEntry__owner
        try:
            session = self.legacy_session_map[old_block.session]
        except KeyError:
            self.importer.print_warning(cformat('%{yellow!}Found zombie session {}').format(old_block.session),
                                        event_id=self.event.id)
            session = self._migrate_session(old_block.session)
        session_block = SessionBlock(session=session, title=convert_to_unicode(old_block.title),
                                     duration=old_block.duration)
        session_block.timetable_entry = TimetableEntry(event_new=self.event, start_dt=old_block.startDate)
        self._migrate_location(old_block, session_block)
        session_block.person_links = list(self._migrate_session_block_persons(old_block))
        self._migrate_timetable_entries(old_block._schedule._entries, session_block)

    def _migrate_location(self, old_entry, new_entry):
        custom_location = (old_entry.places[0] if getattr(old_entry, 'places', None)
                           else getattr(old_entry, 'place', None))
        custom_room = (old_entry.rooms[0] if getattr(old_entry, 'rooms', None)
                       else getattr(old_entry, 'room', None))
        new_entry.inherit_location = not custom_location
        if new_entry.inherit_location:
            return
        # we don't inherit, so let's migrate the data we have
        # address is always allowed
        new_entry.address = fix_broken_string(custom_location.address, True) if custom_location.address else ''
        location_name = fix_broken_string(custom_location.name, True)
        if custom_room:
            room_name = fix_broken_string(custom_room.name, True)
            rb_room = self.importer.room_mapping.get((location_name, room_name))
            # if we have a room from the rb module, we only link this, otherwise we use the (custom) names
            if rb_room:
                new_entry.room = rb_room
            else:
                new_entry.location_name = location_name
                new_entry.room_name = room_name


class EventTimetableImporter(Importer):
    def __init__(self, **kwargs):
        self.default_group_provider = kwargs.pop('default_group_provider')
        self.parallel = kwargs.pop('parallel')
        self.reference_types = kwargs.pop('reference_types')
        super(EventTimetableImporter, self).__init__(**kwargs)
        self.reference_type_map = {}

    @staticmethod
    def decorate_command(command):
        def _process_parallel(ctx, param, value):
            if value is None:
                return None
            n, i = map(int, value.split(':', 1))
            if n <= 1:
                raise click.BadParameter('N must be >1')
            if i not in range(n):
                raise click.BadParameter('I must be in [0..{})'.format(n))
            return n, i

        command = click.option('--default-group-provider', default='legacy-ldap',
                               help="Name of the default group provider")(command)
        command = click.option('-R', '--reference-type', 'reference_types', multiple=True,
                               help="Reference types ('report numbers'). Can be used multiple times "
                                    "to specify multiple reference types")(command)
        command = click.option('-P', '--parallel', metavar='N:I', callback=_process_parallel,
                               help='Parallel mode - migrates only events with `ID mod N = I`. '
                                    'When using this, you need to run the script N times with '
                                    'I being in [0..N)')(command)
        return command

    def has_data(self):
        if self.parallel and self.parallel[1] == 0 and ReferenceType.has_rows():
            return True
        models = (TimetableEntry, Break, Session, SessionBlock, Contribution)
        return any(x.has_rows() for x in models)

    def _load_data(self):
        self.print_step("Loading some data")
        self.room_mapping = _get_room_mapping()
        self.all_users_by_email = {}
        for user in User.query.options(joinedload('_all_emails')):
            if user.is_deleted:
                continue
            for email in user.all_emails:
                self.all_users_by_email[email] = user

    def migrate(self):
        self._load_data()
        self.migrate_reference_types()
        with patch_default_group_provider(self.default_group_provider):
            self.migrate_events()

    def migrate_reference_types(self):
        if self.parallel and self.parallel[1]:
            self.print_step("Loading reference types")
            self.reference_type_map = {r.name: r for r in ReferenceType.query}
            return
        self.print_step("Migrating reference types")
        for name in self.reference_types:
            self.reference_type_map[name] = reftype = ReferenceType(name=name)
            db.session.add(reftype)
            self.print_success(name)
        db.session.commit()

    def migrate_events(self):
        self.print_step("Migrating events")
        for old_event, event in committing_iterator(self._iter_events()):
            mig = TimetableMigration(self, old_event, event)
            try:
                with db.session.begin_nested():
                    with db.session.no_autoflush:
                        mig.run()
                        db.session.flush()
            except Exception:
                self.print_error(cformat('%{red!}MIGRATION FAILED!'), event_id=event.id)
                traceback.print_exc()

    def _iter_events(self):
        it = self.zodb_root['conferences'].itervalues()
        total = len(self.zodb_root['conferences'])
        all_events_query = Event.find(is_deleted=False).options(undefer('_last_friendly_contribution_id'),
                                                                undefer('_last_friendly_session_id'))
        if self.parallel:
            n, i = self.parallel
            it = (e for e in it if int(e.id) % n == i)
            total = int(ceil(total / n))
            all_events_query = all_events_query.filter(Event.id % n == i)
        if self.quiet:
            it = verbose_iterator(it, total, attrgetter('id'), attrgetter('title'))
        all_events = {e.id: e for e in all_events_query}
        for old_event in self.flushing_iterator(it):
            event = all_events.get(int(old_event.id))
            if event is None:
                self.print_error(cformat('%{red!}Event is only in ZODB but not in SQL'), event_id=old_event.id)
                continue
            yield old_event, event

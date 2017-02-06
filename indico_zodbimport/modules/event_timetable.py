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


from __future__ import unicode_literals, division

import itertools
import traceback
from collections import defaultdict
from math import ceil
from operator import attrgetter, itemgetter
from uuid import uuid4

import click
from sqlalchemy.orm import joinedload, undefer, lazyload
from sqlalchemy.orm.attributes import set_committed_value

from indico.core.db import db
from indico.core.db.sqlalchemy.colors import ColorTuple
from indico.core.db.sqlalchemy.principals import EmailPrincipal
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.core.db.sqlalchemy.util.session import update_session_options
# from indico.modules.events.abstracts.models.legacy import LegacyAbstract
from indico.modules.events.abstracts.models.fields import AbstractFieldValue
# from indico.modules.events.abstracts.models.judgments import Judgment
from indico.modules.events.abstracts.settings import abstracts_settings
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.fields import ContributionField, ContributionFieldValue
from indico.modules.events.contributions.models.legacy_mapping import (LegacyContributionMapping,
                                                                       LegacySubContributionMapping)
from indico.modules.events.contributions.models.principals import ContributionPrincipal
from indico.modules.events.contributions.models.persons import (ContributionPersonLink, SubContributionPersonLink,
                                                                AuthorType)
from indico.modules.events.contributions.models.references import ContributionReference, SubContributionReference
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.contributions.models.types import ContributionType
from indico.modules.events.models.events import Event
from indico.modules.events.models.persons import EventPerson, EventPersonLink
from indico.modules.events.models.references import ReferenceType, EventReference
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.legacy_mapping import LegacySessionMapping, LegacySessionBlockMapping
from indico.modules.events.sessions.models.persons import SessionBlockPersonLink
from indico.modules.events.sessions.models.principals import SessionPrincipal
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.timetable.models.breaks import Break
from indico.modules.events.timetable.models.entries import TimetableEntry
from indico.modules.rb import Location, Room
from indico.modules.users import User
from indico.modules.users.legacy import AvatarUserWrapper
from indico.modules.users.models.users import UserTitle
from indico.util.console import cformat, verbose_iterator
from indico.util.date_time import as_utc
from indico.util.string import fix_broken_string, sanitize_email, is_valid_mail
from indico.util.struct.iterables import committing_iterator

from indico_zodbimport import Importer, convert_to_unicode
from indico_zodbimport.util import convert_principal, patch_default_group_provider


PROTECTION_MODE_MAP = {
    -1: ProtectionMode.public,
    0: ProtectionMode.inheriting,
    1: ProtectionMode.protected,
}

USER_TITLE_MAP = {unicode(x.title): x for x in UserTitle}

PERSON_INFO_MAP = {
    '_address': 'address',
    '_affiliation': 'affiliation',
    '_firstName': 'first_name',
    '_surName': 'last_name',
    '_phone': 'phone'
}

AVATAR_PERSON_INFO_MAP = {
    'getAddress': 'address',
    'getAffiliation': 'affiliation',
    'getFirstName': 'first_name',
    'getFamilyName': 'last_name',
    'getPhone': 'phone'
}


def _get_room_mapping():
    return {(r.location.name, r.name): r for r in Room.query.options(lazyload(Room.owner), joinedload(Room.location))}


class TimetableMigration(object):
    def __init__(self, importer, old_event, event):
        self.importer = importer
        self.old_event = old_event
        self.event = event
        self.event_person_map = {}
        self.legacy_session_map = {}
        self.legacy_session_ids_used = set()
        self.legacy_contribution_map = {}
        self.legacy_contribution_type_map = {}
        self.legacy_contribution_field_map = {}
        self.legacy_field_option_id_map = {}
        # we know some relationships are empty; prevent SA from loading them
        set_committed_value(self.event, 'references', [])
        set_committed_value(self.event, 'person_links', [])

    def __repr__(self):
        return '<TimetableMigration({})>'.format(self.event)

    def run(self):
        self.importer.print_success('Importing {}'.format(self.old_event), event_id=self.event.id)
        self.event.references = list(self._process_references(EventReference, self.old_event))
        self._migrate_event_persons()
        self._migrate_event_persons_links()
        self._migrate_contribution_types()
        self._migrate_contribution_fields()
        self._migrate_sessions()
        self._migrate_contributions()
        self._migrate_abstracts()
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
            if isinstance(values, basestring):
                values = [values]
            for value in map(convert_to_unicode, values):
                if value == 'None':
                    self.importer.print_warning(cformat("%{yellow!}Skipping 'None' value"), event_id=self.event.id)
                    continue
                if not self.importer.quiet:
                    self.importer.print_info(cformat(' - %{magenta}{}: %{green!}{}').format(name, value))
                yield reference_cls(reference_type=reference_type, value=value)

    def _process_keywords(self, keywords):
        return map(convert_to_unicode, keywords.splitlines())

    def _create_person(self, old_person, with_event=False, skip_empty_email=False):
        email = getattr(old_person, '_email', None) or getattr(old_person, 'email', None)
        email = sanitize_email(convert_to_unicode(email).lower()) if email else email
        if email and not is_valid_mail(email, False):
            email = None
            if skip_empty_email:
                self.importer.print_warning(cformat('%{yellow!}Skipping invalid email {}').format(email),
                                            event_id=self.event.id)
        if not email and skip_empty_email:
            return None
        person = EventPerson(event_new=self.event if with_event else None,
                             email=email, **self._get_person_data(old_person))
        if not person.first_name and not person.last_name:
            self.importer.print_warning(cformat('%{yellow!}Skipping nameless event person'), event_id=self.event.id)
            return None
        return person

    def _get_person(self, old_person):
        email = getattr(old_person, '_email', None) or getattr(old_person, 'email', None)
        email = sanitize_email(convert_to_unicode(email).lower()) if email else email
        if not is_valid_mail(email, False):
            email = None
        return self.event_person_map.get(email) if email else self._create_person(old_person, with_event=True)

    def _get_person_data(self, old_person):
        data = {}
        if isinstance(old_person, AvatarUserWrapper):
            for old_meth, new_attr in AVATAR_PERSON_INFO_MAP.iteritems():
                data[new_attr] = convert_to_unicode(getattr(old_person, old_meth)())
        else:
            for old_attr, new_attr in PERSON_INFO_MAP.iteritems():
                data[new_attr] = convert_to_unicode(getattr(old_person, old_attr, ''))
        data['_title'] = USER_TITLE_MAP.get(getattr(old_person, '_title', ''), UserTitle.none)
        return data

    def _update_link_data(self, link, data_list):
        for attr in PERSON_INFO_MAP.itervalues():
            value = most_common(data_list, key=itemgetter(attr))
            if value and value != getattr(link, attr):
                setattr(link, attr, value)

    def _migrate_event_persons(self):
        all_persons = defaultdict(list)
        old_people = []
        for chairperson in getattr(self.old_event, '_chairs', []):
            old_people.append(chairperson)
        for old_contrib in self.old_event.contributions.itervalues():
            for speaker in getattr(old_contrib, '_speakers', []):
                old_people.append(speaker)
            for author in getattr(old_contrib, '_primaryAuthors', []):
                old_people.append(author)
            for coauthor in getattr(old_contrib, '_coAuthors', []):
                old_people.append(coauthor)
            for old_subcontrib in old_contrib._subConts:
                for speaker in getattr(old_subcontrib, 'speakers', []):
                    old_people.append(speaker)
        for old_entry in self.old_event._Conference__schedule._entries:
            entry_type = old_entry.__class__.__name__
            if entry_type == 'LinkedTimeSchEntry':
                old_block = old_entry._LinkedTimeSchEntry__owner
                for convener in getattr(old_block, '_conveners', []):
                    old_people.append(convener)
        for old_person in old_people:
            person = self._create_person(old_person, skip_empty_email=True)
            if person:
                user = self.importer.all_users_by_email.get(person.email)
                email = user.email if user else person.email
                all_persons[email].append(person)
        for email, persons in all_persons.iteritems():
            person = EventPerson(email=email,
                                 event_new=self.event,
                                 user=self.importer.all_users_by_email.get(email),
                                 first_name=most_common(persons, key=attrgetter('first_name')),
                                 last_name=most_common(persons, key=attrgetter('last_name')),
                                 _title=most_common(persons, key=attrgetter('_title')),
                                 affiliation=most_common(persons, key=attrgetter('affiliation')),
                                 address=most_common(persons, key=attrgetter('address')),
                                 phone=most_common(persons, key=attrgetter('phone')))
            self.event_person_map[email] = person
            if person.user:
                for user_email in person.user.all_emails:
                    self.event_person_map[user_email] = person
            if not self.importer.quiet:
                msg = cformat('%{magenta!}Event Person%{reset} {}({})').format(person.full_name, person.email)
                self.importer.print_info(msg)

    def _migrate_event_persons_links(self):
        person_link_map = {}
        for chair in getattr(self.old_event, '_chairs', []):
            person = self._get_person(chair)
            if not person:
                continue
            link = person_link_map.get(person)
            if link:
                self.importer.print_warning(
                    cformat('%{yellow!}Duplicated chair "{}" for event').format(person.full_name),
                    event_id=self.event.id
                )
            else:
                link = EventPersonLink(person=person, **self._get_person_data(chair))
                person_link_map[person] = link
                self.event.person_links.append(link)

    def _migrate_contribution_types(self):
        name_map = {}
        for old_ct in self.old_event._contribTypes.itervalues():
            name = convert_to_unicode(old_ct._name)
            existing = name_map.get(name.lower())
            if existing is not None:
                self.importer.print_warning(cformat('%{yellow}Duplicate contribution type name: {}').format(name))
                self.legacy_contribution_type_map[old_ct] = existing
                continue
            ct = ContributionType(name=name, description=convert_to_unicode(old_ct._description))
            name_map[name.lower()] = ct
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
        if old_session.id not in self.legacy_session_ids_used:
            session.legacy_mapping = LegacySessionMapping(event_new=self.event, legacy_session_id=old_session.id)
            self.legacy_session_ids_used.add(old_session.id)
        else:
            self.importer.print_warning(cformat('%{yellow!}Duplicate session id; not adding legacy mapping for {}')
                                        .format(old_session.id), event_id=self.event.id)
        # colors
        try:
            session.colors = ColorTuple(old_session._textColor, old_session._color)
        except (AttributeError, ValueError) as e:
            self.importer.print_warning(cformat('%{yellow}Session has no colors: "{}" [{}]').format(session.title, e),
                                        event_id=self.event.id)
        principals = {}
        # managers / read access
        self._process_ac(SessionPrincipal, principals, ac, allow_emails=True)
        # coordinators
        for submitter in old_session._coordinators.itervalues():
            self._process_principal(SessionPrincipal, principals, submitter, 'Coordinator', roles={'coordinate'})
        self._process_principal_emails(SessionPrincipal, principals, getattr(old_session, '_coordinatorsEmail', []),
                                       'Coordinator', roles={'coordinate'}, allow_emails=True)
        session.acl_entries = set(principals.itervalues())
        return session

    def _migrate_contribution_fields(self):
        try:
            afm = self.old_event.abstractMgr._abstractFieldsMgr
        except AttributeError:
            return
        pos = 0

        content_field = None
        for field in afm._fields:
            # it may happen that there is a second 'content' field (old version schemas)
            # in that case, let's use the first one as description and keep the second one as a field
            if field._id == 'content' and not content_field:
                content_field = field
            else:
                pos += 1
                self._migrate_contribution_field(field, pos)

        if not content_field:
            self.importer.print_warning(
                cformat('%{yellow!}Event has no content field!%{reset}'), event_id=self.event.id)
            return

        def _positive_or_none(value):
            try:
                value = int(value)
            except (TypeError, ValueError):
                return None
            return value if value > 0 else None

        limitation = getattr(content_field, '_limitation', 'chars')
        settings = {
            'is_active': bool(content_field._active),
            'is_required': bool(content_field._isMandatory),
            'max_words': _positive_or_none(content_field._maxLength) if limitation == 'words' else None,
            'max_length': _positive_or_none(content_field._maxLength) if limitation == 'chars' else None
        }
        if settings != abstracts_settings.defaults['description_settings']:
            abstracts_settings.set(self.event, 'description_settings', settings)

    def _migrate_contribution_field(self, old_field, position):
        field_type = old_field.__class__.__name__
        if field_type in ('AbstractTextAreaField', 'AbstractInputField', 'AbstractField'):
            multiline = field_type == 'AbstractTextAreaField' or (field_type == 'AbstractField' and
                                                                  getattr(old_field, '_type', 'textarea') == 'textarea')
            limitation = getattr(old_field, '_limitation', 'chars')
            field_data = {
                'max_length': int(old_field._maxLength) if limitation == 'chars' else None,
                'max_words': int(old_field._maxLength) if limitation == 'words' else None,
                'multiline': multiline
            }
            field_type = 'text'
        elif field_type == 'AbstractSelectionField':
            options = []
            for opt in old_field._options:
                uuid = unicode(uuid4())
                self.legacy_field_option_id_map[old_field._id, int(opt.id)] = uuid
                options.append({'option': convert_to_unicode(opt.value), 'id': uuid, 'is_deleted': False})
            for opt in old_field._deleted_options:
                uuid = unicode(uuid4())
                self.legacy_field_option_id_map[old_field._id, int(opt.id)] = uuid
                options.append({'option': convert_to_unicode(opt.value), 'id': uuid, 'is_deleted': True})
            field_data = {'options': options, 'display_type': 'select'}
            field_type = 'single_choice'
        else:
            self.importer.print_error('Unrecognized field type {}'.format(field_type), event_id=self.event.id)
            return
        if old_field._id in self.legacy_contribution_field_map:
            self.importer.print_warning(
                cformat("%{yellow!}There is already a field with legacy_id '{}')!%{reset}").format(old_field._id),
                event_id=self.event.id)
            return
        field = ContributionField(event_new=self.event, field_type=field_type, is_active=old_field._active,
                                  title=convert_to_unicode(old_field._caption), is_required=old_field._isMandatory,
                                  field_data=field_data, position=position, legacy_id=old_field._id)
        self.legacy_contribution_field_map[old_field._id] = field
        if not self.importer.quiet:
            self.importer.print_info(cformat('%{green}Contribution field%{reset} {}').format(field.title))

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

    def _migrate_abstracts(self):
        for old_abstract in self.old_event.abstractMgr._abstracts.itervalues():
            self._migrate_abstract(old_abstract)

    def _migrate_contribution(self, old_contrib, friendly_id):
        ac = old_contrib._Contribution__ac
        description = old_contrib._fields.get('content', '')
        description = convert_to_unicode(getattr(description, 'value', description))  # str or AbstractFieldContent
        status = getattr(old_contrib, '_status', None)
        status_class = status.__class__.__name__ if status else None

        contrib = Contribution(event_new=self.event, friendly_id=friendly_id,
                               title=convert_to_unicode(old_contrib.title),
                               description=description, duration=old_contrib.duration,
                               protection_mode=PROTECTION_MODE_MAP[ac._accessProtection],
                               board_number=convert_to_unicode(getattr(old_contrib, '_boardNumber', '')),
                               keywords=self._process_keywords(old_contrib._keywords),
                               is_deleted=(status_class == 'ContribStatusWithdrawn'))
        if old_contrib._track is not None:
            contrib.track_id = int(old_contrib._track.id)
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
        contrib.person_links = list(self._migrate_contribution_person_links(old_contrib))
        # references ("report numbers")
        contrib.references = list(self._process_references(ContributionReference, old_contrib))
        # contribution/abstract fields
        contrib.field_values = list(self._migrate_contribution_field_values(old_contrib))
        contrib.subcontributions = [self._migrate_subcontribution(old_contrib, old_subcontrib, pos)
                                    for pos, old_subcontrib in enumerate(old_contrib._subConts, 1)]
        contrib._last_friendly_subcontribution_id = len(contrib.subcontributions)
        return contrib

    def _migrate_abstract(self, old_abstract):
        description = getattr(old_abstract, '_fields', {}).get('content', '')
        description = convert_to_unicode(getattr(description, 'value', description))  # str or AbstractFieldContent
        old_contribution = getattr(old_abstract, '_contribution', None)
        type_ = old_abstract._contribTypes[0]
        try:
            type_id = self.legacy_contribution_type_map[type_].id if type_ else None
        except KeyError:
            self.importer.print_warning(cformat('%{yellow!}Abstract {} - invalid contrib type {}, setting to None')
                                        .format(old_abstract._id,
                                                convert_to_unicode(getattr(type_, '_name', str(type_)))),
                                        event_id=self.event.id)
            type_id = None

        accepted_type_id = None
        accepted_track_id = None

        if old_contribution:
            assert old_contribution.__class__.__name__ == 'AcceptedContribution'
            if old_abstract._currentStatus.__class__.__name__ == 'AbstractStatusAccepted':
                old_contrib_type = old_abstract._currentStatus._contribType
                try:
                    accepted_type_id = (self.legacy_contribution_type_map[old_contrib_type].id
                                        if old_contrib_type else None)
                except KeyError:
                    self.importer.print_warning(
                        cformat('%{yellow!}Contribution {} - invalid contrib type {}, setting to None')
                        .format(old_contribution.id, convert_to_unicode(old_contrib_type._name)),
                        event_id=self.event.id)

                accepted_track = old_abstract._currentStatus._track
                accepted_track_id = int(accepted_track.id) if accepted_track else None

        abstract = LegacyAbstract(event_new=self.event, friendly_id=old_abstract._id,
                            description=description, type_id=type_id, accepted_track_id=accepted_track_id,
                            accepted_type_id=accepted_type_id)

        if old_contribution and old_contribution.id:
            abstract.contribution = self.legacy_contribution_map[old_contribution]

        if not self.importer.quiet:
            self.importer.print_info(cformat('%{cyan}Abstract%{reset} {}').format(abstract.friendly_id))
        # contribution/abstract fields
        abstract.field_values = list(self._migrate_abstract_field_values(old_abstract))
        abstract.judgments = list(self._migrate_abstract_judgments(old_abstract))
        return abstract

    def _migrate_abstract_judgments(self, old_abstract):
        if not hasattr(old_abstract, '_trackJudgementsHistorical'):
            self.importer.print_warning(
                cformat('%{blue!}Abstract {} {yellow}had no judgment history!%{reset}').format(old_abstract._id),
                event_id=self.event.id)
            return

        history = old_abstract._trackJudgementsHistorical
        if not hasattr(history, 'iteritems'):
            self.importer.print_warning('Abstract {} had corrupt judgment history ({}).'.format(old_abstract._id,
                                                                                                history),
                                        event_id=self.event.id)
            return
        for track_id, judgments in history.iteritems():
            seen_judges = set()
            for old_judgment in judgments:
                judge = old_judgment._responsible.user if old_judgment._responsible else None
                if not judge:
                    self.importer.print_warning(
                        cformat('%{blue!}Abstract {} {yellow}had an empty judge ({})!%{reset}').format(
                            old_abstract._id, old_judgment), event_id=self.event.id)
                    continue
                elif judge in seen_judges:
                    self.importer.print_warning(
                        cformat("%{blue!}Abstract {}: {yellow}judge '{}' seen more than once ({})!%{reset}")
                        .format(old_abstract._id, judge, old_judgment), event_id=self.event.id)
                    continue

                new_judgment = Judgment(creation_dt=as_utc(old_judgment._date),
                                        track_id=old_judgment._track.id, judge=judge)

                seen_judges.add(judge)
                if old_judgment.__class__.__name__ == 'AbstractAcceptance' and old_judgment._contribType:
                    contrib_type = old_judgment._contribType
                    try:
                        new_judgment.accepted_type = self.legacy_contribution_type_map[contrib_type]
                    except KeyError:
                        self.importer.print_warning(
                            cformat("%{blue!}Abstract {}: {yellow}contribution type '{}' unknown!%{reset}")
                            .format(old_abstract._id, getattr(contrib_type, '_name', contrib_type)),
                            event_id=self.event.id)
                yield new_judgment

    def _migrate_contribution_field_values(self, old_contrib):
        fields = dict(old_contrib._fields)
        fields.pop('content', None)
        for field_id, field_content in fields.iteritems():
            value = getattr(field_content, 'value', field_content)
            if isinstance(value, list):
                # legacy data, apparently there was a 'keywords' abstract field type once
                value = ', '.join(value)
            value = convert_to_unicode(value)
            if not value:
                continue
            try:
                new_field = self.legacy_contribution_field_map[field_id]
            except KeyError:
                self.importer.print_warning(cformat('%{yellow!}Contribution field "{}" does not exist')
                                            .format(field_id),
                                            event_id=self.event.id)
                continue
            new_value = self._process_contribution_field_value(field_id, value, new_field, ContributionFieldValue)
            if new_value:
                if not self.importer.quiet:
                    self.importer.print_info(cformat('%{green} - [field]%{reset} {}: {}').format(new_field.title,
                                                                                                 new_value.data))
                yield new_value

    def _migrate_abstract_field_values(self, old_abstract):
        fields = dict(getattr(old_abstract, '_fields', {}))
        fields.pop('content', None)
        for field_id, field_content in fields.iteritems():
            value = convert_to_unicode(getattr(field_content, 'value', field_content))
            if not value:
                continue
            try:
                new_field = self.legacy_contribution_field_map[field_id]
            except KeyError:
                self.importer.print_warning(cformat('%{yellow!}Contribution field "{}" does not exist')
                                            .format(field_id),
                                            event_id=self.event.id)
                continue
            new_value = self._process_contribution_field_value(field_id, value, new_field, AbstractFieldValue)
            if new_value:
                if not self.importer.quiet:
                    self.importer.print_info(cformat('%{green} - [field]%{reset} {}: {}').format(new_field.title,
                                                                                                 new_value.data))
                yield new_value

    def _process_contribution_field_value(self, old_field_id, old_value, new_field, field_class):
        if new_field.field_type == 'text':
            data = convert_to_unicode(old_value)
            return field_class(contribution_field=new_field, data=data)
        elif new_field.field_type == 'single_choice':
            data = self.legacy_field_option_id_map[old_field_id, int(old_value)]
            return field_class(contribution_field=new_field, data=data)
        else:
            raise ValueError('Unexpected field type: {}'.format(new_field.field_type))

    def _migrate_subcontribution(self, old_contrib, old_subcontrib, position):
        subcontrib = SubContribution(position=position, friendly_id=position, duration=old_subcontrib.duration,
                                     title=convert_to_unicode(old_subcontrib.title),
                                     description=convert_to_unicode(old_subcontrib.description))
        if not self.importer.quiet:
            self.importer.print_info(cformat('  %{cyan!}SubContribution%{reset} {}').format(subcontrib.title))
        subcontrib.legacy_mapping = LegacySubContributionMapping(event_new=self.event,
                                                                 legacy_contribution_id=old_contrib.id,
                                                                 legacy_subcontribution_id=old_subcontrib.id)
        subcontrib.references = list(self._process_references(SubContributionReference, old_subcontrib))
        subcontrib.person_links = list(self._migrate_subcontribution_person_links(old_subcontrib))
        return subcontrib

    def _migrate_contribution_person_links(self, old_entry):
        person_link_map = {}
        person_link_data_map = defaultdict(list)
        for speaker in getattr(old_entry, '_speakers', []):
            person = self._get_person(speaker)
            if not person:
                continue
            person_link_data = self._get_person_data(speaker)
            person_link_data_map[person].append(person_link_data)
            link = person_link_map.get(person)
            if link:
                self._update_link_data(link, person_link_data_map[person])
                link.is_speaker = True
            else:
                link = ContributionPersonLink(person=person, is_speaker=True, **person_link_data)
                person_link_map[person] = link
                yield link
        for author in getattr(old_entry, '_primaryAuthors', []):
            person = self._get_person(author)
            if not person:
                continue
            person_link_data = self._get_person_data(author)
            person_link_data_map[person].append(person_link_data)
            link = person_link_map.get(person)
            if link:
                self._update_link_data(link, person_link_data_map[person])
                link.author_type = AuthorType.primary
            else:
                link = ContributionPersonLink(person=person, author_type=AuthorType.primary, **person_link_data)
                person_link_map[person] = link
                yield link
        for coauthor in getattr(old_entry, '_coAuthors', []):
            person = self._get_person(coauthor)
            if not person:
                continue
            person_link_data = self._get_person_data(coauthor)
            person_link_data_map[person].append(person_link_data)
            link = person_link_map.get(person)
            if link:
                self._update_link_data(link, person_link_data_map[person])
                if link.author_type == AuthorType.primary:
                    self.importer.print_warning(cformat('%{yellow!}Primary author "{}" is also co-author')
                                                .format(person.full_name), event_id=self.event.id)
                else:
                    link.author_type = AuthorType.secondary
            else:
                link = ContributionPersonLink(person=person, author_type=AuthorType.secondary, **person_link_data)
                person_link_map[person] = link
                yield link

    def _migrate_subcontribution_person_links(self, old_entry):
        person_link_map = {}
        person_link_data_map = defaultdict(list)
        for speaker in getattr(old_entry, 'speakers', []):
            person = self._get_person(speaker)
            if not person:
                continue
            person_link_data = self._get_person_data(speaker)
            person_link_data_map[person].append(person_link_data)
            link = person_link_map.get(person)
            if link:
                self._update_link_data(link, person_link_data_map[person])
                self.importer.print_warning(
                    cformat('%{yellow!}Duplicated speaker "{}" for sub-contribution').format(person.full_name),
                    event_id=self.event.id
                )
            else:
                link = SubContributionPersonLink(person=person, **person_link_data)
                person_link_map[person] = link
                yield link

    def _migrate_session_block_person_links(self, old_entry):
        person_link_map = {}
        person_link_data_map = defaultdict(list)
        for convener in getattr(old_entry, '_conveners', []):
            person = self._get_person(convener)
            if not person:
                continue
            person_link_data = self._get_person_data(convener)
            person_link_data_map[person].append(person_link_data)
            link = person_link_map.get(person)
            if link:
                self._update_link_data(link, person_link_data_map[person])
                self.importer.print_warning(
                    cformat('%{yellow!}Duplicated session block convener "{}"').format(person.full_name),
                    event_id=self.event.id
                )
            else:
                link = SessionBlockPersonLink(person=person, **person_link_data)
                person_link_map[person] = link
                yield link

    def _migrate_timetable(self):
        if not self.importer.quiet:
            self.importer.print_info(cformat('%{green}Timetable...'))
        self._migrate_timetable_entries(self.old_event._Conference__schedule._entries)

    def _migrate_timetable_entries(self, old_entries, session_block=None):
        for old_entry in old_entries:
            item_type = old_entry.__class__.__name__
            if item_type == 'ContribSchEntry':
                entry = self._migrate_contribution_timetable_entry(old_entry, session_block)
            elif item_type == 'BreakTimeSchEntry':
                entry = self._migrate_break_timetable_entry(old_entry, session_block)
            elif item_type == 'LinkedTimeSchEntry':
                parent = old_entry._LinkedTimeSchEntry__owner
                parent_type = parent.__class__.__name__
                if parent_type == 'Contribution':
                    self.importer.print_warning(cformat('%{yellow!}Found LinkedTimeSchEntry for contribution'),
                                                event_id=self.event.id)
                    entry = self._migrate_contribution_timetable_entry(old_entry, session_block)
                elif parent_type != 'SessionSlot':
                    self.importer.print_error(cformat('%{red!}Found LinkedTimeSchEntry for {}').format(parent_type),
                                              event_id=self.event.id)
                    continue
                else:
                    assert session_block is None
                    entry = self._migrate_block_timetable_entry(old_entry)
            else:
                raise ValueError('Unexpected item type: ' + item_type)
            if session_block:
                if entry.start_dt < session_block.timetable_entry.start_dt:
                    self.importer.print_warning(cformat('%{yellow!}Block boundary (start) violated; extending block '
                                                        'from {} to {}').format(session_block.timetable_entry.start_dt,
                                                                                entry.start_dt),
                                                event_id=self.event.id)
                    session_block.timetable_entry.start_dt = entry.start_dt
                if entry.end_dt > session_block.timetable_entry.end_dt:
                    self.importer.print_warning(cformat('%{yellow!}Block boundary (end) violated; extending block '
                                                        'from {} to {}').format(session_block.timetable_entry.end_dt,
                                                                                entry.end_dt),
                                                event_id=self.event.id)
                    session_block.duration += entry.end_dt - session_block.timetable_entry.end_dt

    def _migrate_contribution_timetable_entry(self, old_entry, session_block=None):
        old_contrib = old_entry._LinkedTimeSchEntry__owner
        contrib = self.legacy_contribution_map[old_contrib]
        contrib.timetable_entry = TimetableEntry(event_new=self.event, start_dt=old_contrib.startDate)
        self._migrate_location(old_contrib, contrib)
        if session_block:
            contrib.session = session_block.session
            contrib.session_block = session_block
            contrib.timetable_entry.parent = session_block.timetable_entry
        return contrib.timetable_entry

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
        return break_.timetable_entry

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
        if session.legacy_mapping is not None:
            session_block.legacy_mapping = LegacySessionBlockMapping(event_new=self.event,
                                                                     legacy_session_id=old_block.session.id,
                                                                     legacy_session_block_id=old_block.id)
        self._migrate_location(old_block, session_block)
        session_block.person_links = list(self._migrate_session_block_person_links(old_block))
        self._migrate_timetable_entries(old_block._schedule._entries, session_block)
        return session_block.timetable_entry

    def _migrate_location(self, old_entry, new_entry):
        custom_location = (old_entry.places[0] if getattr(old_entry, 'places', None)
                           else getattr(old_entry, 'place', None))
        custom_room = (old_entry.rooms[0] if getattr(old_entry, 'rooms', None)
                       else getattr(old_entry, 'room', None))
        new_entry.inherit_location = not custom_location and not custom_room
        if new_entry.inherit_location:
            return
        # we don't inherit, so let's migrate the data we have
        # address is always allowed
        if not custom_location:
            custom_location = self._get_parent_location(old_entry, attr='places')
        if not custom_room:
            custom_room = self._get_parent_location(old_entry, attr='rooms')
        new_entry.address = (convert_to_unicode(fix_broken_string(custom_location.address, True))
                             if custom_location and custom_location.address else '')
        location_name = (convert_to_unicode(fix_broken_string(custom_location.name, True))
                         if custom_location and custom_location.name else '')
        if custom_room:
            room_name = convert_to_unicode(fix_broken_string(custom_room.name, True))
            rb_room = self.importer.room_mapping.get((location_name, room_name))
            # if we have a room from the rb module, we only link this, otherwise we use the (custom) names
            if rb_room:
                new_entry.room = rb_room
            else:
                new_entry.venue_name = location_name
                new_entry.room_name = room_name
        venue = self.importer.venue_mapping.get(new_entry.venue_name)
        if venue is not None:
            # store proper reference to the venue if it's a predefined one
            new_entry.venue = venue
            new_entry.venue_name = ''

    def _get_parent_location(self, obj, attr):
        type_ = obj.__class__.__name__
        if type_ == 'SessionSlot':
            conf = obj.session.conference
            return getattr(conf, attr)[0] if getattr(conf, attr, None) else None
        elif type_ in ('BreakTimeSchEntry', 'Contribution', 'AcceptedContribution'):
            if type_ == 'AcceptedContribution':
                contrib_parent = obj._session
                if getattr(contrib_parent, attr, None):
                    return getattr(contrib_parent, attr)[0]
                else:
                    owner = contrib_parent.conference
            elif type_ == 'Contribution':
                contrib_parent = obj.parent
                if attr == 'places' and contrib_parent:
                    places = getattr(contrib_parent, attr, None)
                    return getattr(contrib_parent, 'place', None) if not places else places[0]
                if attr == 'rooms' and contrib_parent:
                    rooms = getattr(contrib_parent, attr, None)
                    return getattr(contrib_parent, 'room', None) if not rooms else rooms[0]
            elif type_ == 'BreakTimeSchEntry':
                owner = obj._sch._owner
            return self._get_parent_location(owner, attr)
        elif type_ == 'Conference':
            return getattr(obj, attr)[0] if getattr(obj, attr, None) else None
        elif type_ == 'Session':
            return self._get_parent_location(obj.conference, attr)


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
        if self.parallel and self.parallel[1] == 0 and ReferenceType.query.has_rows():
            return True
        models = (TimetableEntry, Break, Session, SessionBlock, Contribution, LegacyAbstract, Judgment)
        return any(x.query.has_rows() for x in models)

    def _load_data(self):
        self.print_step("Loading some data")
        self.room_mapping = _get_room_mapping()
        self.venue_mapping = {location.name: location for location in Location.query}
        self.all_users_by_email = {}
        for user in User.query.options(joinedload('_all_emails')):
            if user.is_deleted:
                continue
            for email in user.all_emails:
                self.all_users_by_email[email] = user

    def migrate(self):
        update_session_options(db, {'expire_on_commit': False})
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
                raw_input('Press ENTER to continue')

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


def most_common(iterable, key=None):
    """Return the most common element of an iterable."""
    groups = itertools.groupby(sorted(iterable), key=key)
    return max(groups, key=lambda x: sum(1 for _ in x[1]))[0]

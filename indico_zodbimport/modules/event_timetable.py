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

import click
from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.core.db.sqlalchemy.colors import ColorTuple
from indico.core.db.sqlalchemy.principals import EmailPrincipal
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.principals import ContributionPrincipal
from indico.modules.events.contributions.models.persons import (ContributionPersonLink, SubContributionPersonLink,
                                                                AuthorType)
from indico.modules.events.contributions.models.references import ContributionReference, SubContributionReference
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.models.events import Event
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.models.references import ReferenceType, EventReference
from indico.modules.events.sessions.models.blocks import SessionBlock
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
        self.legacy_session_map = {}
        self.legacy_contribution_map = {}
        self.legacy_contribution_person_map = {}

    def __repr__(self):
        return '<TimetableMigration({})>'.format(self.event)

    def run(self):
        self.importer.print_success('Importing {}'.format(self.old_event), event_id=self.event.id)
        self.event.references = list(self._process_references(EventReference, self.old_event))
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

    def _migrate_sessions(self):
        for old_session in self.old_event.sessions.itervalues():
            self._migrate_session(old_session)

    def _migrate_session(self, old_session):
        ac = old_session._Session__ac
        session = Session(event_new=self.event, title=convert_to_unicode(old_session.title),
                          colors=ColorTuple(old_session._textColor, old_session._color),
                          default_contribution_duration=old_session._contributionDuration,
                          protection_mode=PROTECTION_MODE_MAP[ac._accessProtection])
        if not self.importer.quiet:
            self.importer.print_info(cformat('%{blue!}Session%{reset} {}').format(session.title))
        self.legacy_session_map[old_session] = session
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
        for old_contrib in self.old_event.contributions.itervalues():
            self._migrate_contribution(old_contrib)

    def _migrate_contribution(self, old_contrib):
        ac = old_contrib._Contribution__ac
        description = old_contrib._fields.get('content', '')
        description = convert_to_unicode(getattr(description, 'value', description))  # str or AbstractFieldContent
        contrib = Contribution(event_new=self.event, title=convert_to_unicode(old_contrib.title),
                               description=description, duration=old_contrib.duration,
                               protection_mode=PROTECTION_MODE_MAP[ac._accessProtection],
                               keywords=self._process_keywords(old_contrib._keywords))
        if not self.importer.quiet:
            self.importer.print_info(cformat('%{cyan}Contribution%{reset} {}').format(contrib.title))
        self.legacy_contribution_map[old_contrib] = contrib
        principals = {}
        # managers / read access
        self._process_ac(ContributionPrincipal, principals, ac)
        # submitters
        for submitter in old_contrib._submitters:
            self._process_principal(ContributionPrincipal, principals, submitter, 'Submitter', roles={'submit'})
        self._process_principal_emails(ContributionPrincipal, principals, getattr(old_contrib, '_submittersEmail', []),
                                       'Submitter', roles={'submit'})
        contrib.acl_entries = set(principals.itervalues())
        # speakers, authors and co-authors
        contrib.person_links = list(self._migrate_contribution_persons(old_contrib))
        contrib.references = list(self._process_references(ContributionReference, old_contrib))
        contrib.subcontributions = [self._migrate_subcontribution(old_subcontrib, pos)
                                    for pos, old_subcontrib in enumerate(old_contrib._subConts, 1)]

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
            person = self._migrate_contribution_person(speaker)
            link = person_link_map.get(person)
            if link:
                link.is_speaker = True
            else:
                link = ContributionPersonLink(person=person, is_speaker=True)
                person_link_map[person] = link
                yield link
        for author in getattr(old_entry, '_primaryAuthors', []):
            person = self._migrate_contribution_person(author)
            link = person_link_map.get(person)
            if link:
                link.author_type = AuthorType.primary
            else:
                link = ContributionPersonLink(person=person, author_type=AuthorType.primary)
                person_link_map[person] = link
                yield link
        for coauthor in getattr(old_entry, '_coAuthors', []):
            person = self._migrate_contribution_person(coauthor)
            link = person_link_map.get(person)
            if link:
                if link.author_type == AuthorType.primary:
                    self.importer.print_warning('Primary author "{}" is also co-author'.format(person.full_name),
                                                event_id=self.event.id)
                else:
                    link.author_type = AuthorType.secondary
            else:
                link = ContributionPersonLink(person=person, author_type=AuthorType.secondary)
                person_link_map[person] = link
                yield link

    def _migrate_subcontribution_persons(self, old_entry):
        person_link_map = {}
        for speaker in getattr(old_entry, 'speakers', []):
            person = self._migrate_contribution_person(speaker)
            link = person_link_map.get(person)
            if link:
                self.importer.print_warning(
                    cformat('%{yellow!}Duplicated speaker {} for sub-contribution').format(person.full_name),
                    event_id=self.event.id
                )
            else:
                link = SubContributionPersonLink(person=person)
                person_link_map[person] = link
                yield link

    def _migrate_contribution_person(self, old_person):
        first_name = convert_to_unicode(getattr(old_person, '_firstName', ''))
        last_name = convert_to_unicode(getattr(old_person, '_surName', ''))
        email = getattr(old_person, '_email', '')
        affiliation = convert_to_unicode(getattr(old_person, '_affiliation', ''))
        key = (first_name, last_name, email, affiliation)
        existing_person = self.legacy_contribution_person_map.get(key)
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
            person.email = sanitize_email(convert_to_unicode(email).lower()) if email else ''
        self.legacy_contribution_person_map[map_key] = person

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
        all_events_query = Event.find(is_deleted=False)
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

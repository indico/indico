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


from __future__ import unicode_literals

import traceback
from operator import attrgetter

import click
from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.core.db.sqlalchemy.colors import ColorTuple
from indico.core.db.sqlalchemy.principals import EmailPrincipal
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.principals import ContributionPrincipal
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.models.events import Event
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.principals import SessionPrincipal
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.timetable.models.breaks import Break
from indico.modules.events.timetable.models.entries import TimetableEntry
from indico.modules.users import User
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


class TimetableMigration(object):
    def __init__(self, importer, old_event, event):
        self.importer = importer
        self.old_event = old_event
        self.event = event
        self.legacy_session_map = {}
        self.legacy_contribution_map = {}

    def __repr__(self):
        return '<TimetableMigration({})>'.format(self.event)

    def run(self):
        self.importer.print_success('Importing {}'.format(self.old_event), event_id=self.event.id)
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
                                            always=False)
        return principal

    def _process_principal(self, principal_cls, principals, legacy_principal, name, read_access=None, full_access=None,
                           roles=None):
        if isinstance(legacy_principal, basestring):
            user = self.importer.all_users_by_email.get(legacy_principal)
            principal = user or EmailPrincipal(legacy_principal)
        else:
            principal = self._convert_principal(legacy_principal)
        if principal is None:
            self.importer.print_warning(cformat('%{yellow}{} does not exist:%{reset} {}')
                                        .format(name, legacy_principal), event_id=self.event.id)
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
                                  roles=None):
        emails = {sanitize_email(convert_to_unicode(email).lower()) for email in emails}
        emails = {email for email in emails if is_valid_mail(email, False)}
        for email in emails:
            self._process_principal(principal_cls, principals, email, name, read_access, full_access, roles)

    def _process_ac(self, principal_cls, principals, ac):
        # read access
        for principal in ac.allowed:
            self._process_principal(principal_cls, principals, principal, 'Access', read_access=True)
        # email-based read access
        emails = getattr(ac, 'allowedEmail', [])
        self._process_principal_emails(principal_cls, principals, emails, 'Access', read_access=True)
        # managers
        for manager in ac.managers:
            self._process_principal(principal_cls, principals, manager, 'Manager', full_access=True)
        # email-based managers
        emails = getattr(ac, 'managersEmail', [])
        self._process_principal_emails(principal_cls, principals, emails, 'Manager', full_access=True)

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
        self._process_ac(SessionPrincipal, principals, ac)
        # coordinators
        for submitter in old_session._coordinators.itervalues():
            self._process_principal(SessionPrincipal, principals, submitter, 'Coordinator', roles={'coordinate'})
        self._process_principal_emails(SessionPrincipal, principals, getattr(old_session, '_coordinatorsEmail', []),
                                       'Coordinator', roles={'coordinate'})
        session.acl_entries = set(principals.itervalues())
        return session

    def _migrate_contributions(self):
        for old_contrib in self.old_event.contributions.itervalues():
            self._migrate_contribution(old_contrib)

    def _migrate_contribution(self, old_contrib):
        ac = old_contrib._Contribution__ac
        contrib = Contribution(event_new=self.event, title=convert_to_unicode(old_contrib.title),
                               description=convert_to_unicode(old_contrib.description), duration=old_contrib.duration,
                               protection_mode=PROTECTION_MODE_MAP[ac._accessProtection])
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
        contrib.subcontributions = [self._migrate_subcontribution(old_subcontrib, pos)
                                    for pos, old_subcontrib in enumerate(old_contrib._subConts, 1)]

    def _migrate_subcontribution(self, old_subcontrib, position):
        subcontrib = SubContribution(position=position, friendly_id=position, duration=old_subcontrib.duration,
                                     title=convert_to_unicode(old_subcontrib.title),
                                     description=convert_to_unicode(old_subcontrib.description))
        if not self.importer.quiet:
            self.importer.print_info(cformat('  %{cyan!}SubContribution%{reset} {}').format(subcontrib.title))
        return subcontrib

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
        super(EventTimetableImporter, self).__init__(**kwargs)

    @staticmethod
    def decorate_command(command):
        command = click.option('--default-group-provider', default='legacy-ldap',
                               help="Name of the default group provider")(command)
        return command

    def has_data(self):
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
        with patch_default_group_provider(self.default_group_provider):
            self.migrate_events()

    def migrate_events(self):
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
        if self.quiet:
            it = verbose_iterator(it, len(self.zodb_root['conferences']), attrgetter('id'), attrgetter('title'))
        all_events = {e.id: e for e in Event.find_all(is_deleted=False)}
        for old_event in self.flushing_iterator(it):
            event = all_events.get(int(old_event.id))
            if event is None:
                self.print_error(cformat('%{red!}Event is only in ZODB but not in SQL'), event_id=old_event.id)
                continue
            yield old_event, event

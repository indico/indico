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

from operator import attrgetter

import click
from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import EmailPrincipal
from indico.modules.events import Event
from indico.modules.events.models.principals import EventPrincipal
from indico.modules.users import User
from indico.util.console import verbose_iterator, cformat
from indico.util.string import is_valid_mail, sanitize_email
from indico.util.struct.iterables import committing_iterator
from indico_zodbimport import Importer, convert_to_unicode
from indico_zodbimport.util import patch_default_group_provider, convert_principal


class EventManagerImporter(Importer):
    def __init__(self, **kwargs):
        self.default_group_provider = kwargs.pop('default_group_provider')
        self.janitor_user_id = kwargs.pop('janitor_user_id')
        super(EventManagerImporter, self).__init__(**kwargs)

    @staticmethod
    def decorate_command(command):
        command = click.option('--janitor-user-id', type=int, required=True,
                               help="The ID of the Janitor user")(command)
        command = click.option('--default-group-provider', default='legacy-ldap',
                               help="Name of the default group provider")(command)
        return command

    def has_data(self):
        return EventPrincipal.query.has_rows()

    def migrate(self):
        self.janitor = User.get_one(self.janitor_user_id)
        # keep all users in memory to avoid extra queries.
        # the assignment is on purpose to stop the gc from throwing the dict away
        # immediately after retrieving it
        _all_users = User.query.options(joinedload('_all_emails')).all()
        self.all_users_by_email = {}
        for user in _all_users:
            if user.is_deleted:
                continue
            for email in user.all_emails:
                self.all_users_by_email[email] = user

        with patch_default_group_provider(self.default_group_provider):
            with db.session.no_autoflush:
                self.migrate_event_managers()

    def convert_principal(self, old_principal):
        principal = convert_principal(old_principal)
        if (principal is None and old_principal.__class__.__name__ in ('Avatar', 'AvatarUserWrapper') and
                'email' in old_principal.__dict__):
            email = old_principal.__dict__['email'].lower()
            principal = self.all_users_by_email.get(email)
            if principal is not None:
                self.print_warning('Using {} for {} (matched via {})'.format(principal, old_principal, email),
                                   always=False)
        return principal

    def process_principal(self, event, principals, legacy_principal, name, color, full_access=None, roles=None):
        if isinstance(legacy_principal, basestring):
            user = self.all_users_by_email.get(legacy_principal)
            principal = user or EmailPrincipal(legacy_principal)
        else:
            principal = self.convert_principal(legacy_principal)
        if principal is None:
            self.print_warning(cformat('%%{%s}{}%%{reset}%%{yellow} does not exist:%%{reset} {}' % color)
                               .format(name, legacy_principal), event_id=event.id)
            return
        try:
            entry = principals[principal]
        except KeyError:
            entry = EventPrincipal(event_id=event.id, principal=principal, full_access=False, roles=[])
            principals[principal] = entry
        if full_access:
            entry.full_access = True
        if roles:
            entry.roles = sorted(set(entry.roles) | set(roles))
        if not self.quiet:
            self.print_msg(cformat('    - %%{%s}[{}]%%{reset} {}' % color).format(name.lower(), principal))
        return principal

    def process_emails(self, event, principals, emails, name, color, full_access=None, roles=None):
        emails = {sanitize_email(convert_to_unicode(email).lower()) for email in emails}
        emails = {email for email in emails if is_valid_mail(email, False)}
        for email in emails:
            self.process_principal(event, principals, email, name, color, full_access, roles)

    def migrate_event_managers(self):
        self.print_step('migrating event managers/creators')
        creator_updates = []
        for event in committing_iterator(self._iter_events(), 5000):
            self.print_success('', event_id=event.id)
            ac = event._Conference__ac
            entries = {}
            # add creator as a manager
            try:
                creator = event._Conference__creator
            except AttributeError:
                # events created after the removal of the `self.__creator` assignment
                # should happen only on dev machines
                self.print_error(cformat('%{red!}Event has no creator attribute'), event_id=event.id)
            else:
                user = self.process_principal(event, entries, creator, 'Creator', 'green!', full_access=True)
                if user:
                    creator_updates.append({'event_id': int(event.id), 'creator_id': user.id})
            # add managers
            for manager in ac.managers:
                self.process_principal(event, entries, manager, 'Manager', 'blue!', full_access=True)
            # add email-based managers
            emails = getattr(ac, 'managersEmail', [])
            self.process_emails(event, entries, emails, 'Manager', 'green', full_access=True)
            # add registrars
            for registrar in getattr(event, '_Conference__registrars', []):
                self.process_principal(event, entries, registrar, 'Registrar', 'cyan', roles={'registration'})
            # add submitters
            for submitter in getattr(ac, 'submitters', []):
                self.process_principal(event, entries, submitter, 'Submitter', 'magenta!', roles={'submit'})
            # email-based (pending) submitters
            pqm = getattr(event, '_pendingQueuesMgr', None)
            if pqm is not None:
                emails = set(getattr(pqm, '_pendingConfSubmitters', []))
                self.process_emails(event, entries, emails, 'Submitter', 'magenta', roles={'submit'})
            db.session.add_all(entries.itervalues())
        # assign creators
        if creator_updates:
            self.print_step('saving event creators')
            stmt = (Event.__table__.update()
                    .where(Event.id == db.bindparam('event_id'))
                    .values(creator_id=db.bindparam('creator_id')))
            db.session.execute(stmt, creator_updates)
        updated = Event.find(Event.creator_id == None).update({Event.creator_id: self.janitor.id})  # noqa
        db.session.commit()
        self.print_success('Set the janitor user {} for {} events'.format(self.janitor, updated), always=True)

    def _iter_events(self):
        it = self.zodb_root['conferences'].itervalues()
        if self.quiet:
            it = verbose_iterator(it, len(self.zodb_root['conferences']), attrgetter('id'), attrgetter('title'))
        event_ids = {id_ for id_, in db.session.query(Event.id)}
        for event in self.flushing_iterator(it):
            if int(event.id) not in event_ids:
                self.print_error(cformat('%{red!}Event not found in DB'), event_id=event.id)
                continue
            yield event

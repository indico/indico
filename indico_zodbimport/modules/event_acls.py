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

from math import ceil
from operator import attrgetter

import click
from sqlalchemy.orm import joinedload

from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events import Event
from indico.modules.networks.models.networks import IPNetworkGroup
from indico.modules.users import User
from indico.util.console import verbose_iterator, cformat
from indico.util.struct.iterables import committing_iterator
from indico_zodbimport import Importer
from indico_zodbimport.util import patch_default_group_provider, convert_principal, convert_to_unicode


class EventACLImporter(Importer):
    def __init__(self, **kwargs):
        self.default_group_provider = kwargs.pop('default_group_provider')
        self.parallel = kwargs.pop('parallel')
        self.all_users_by_email = {}
        self.domains_map = {}
        super(EventACLImporter, self).__init__(**kwargs)

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

        command = click.option('--default-group-provider', required=True,
                               help="Name of the default group provider")(command)
        command = click.option('-P', '--parallel', metavar='N:I', callback=_process_parallel,
                               help='Parallel mode - migrates only events with `ID mod N = I`. '
                                    'When using this, you need to run the script N times with '
                                    'I being in [0..N)')(command)
        return command

    @no_autoflush
    def migrate(self):
        self.domains_map = {ipng.name.lower(): ipng for ipng in IPNetworkGroup.query}
        all_users_query = User.query.options(joinedload('_all_emails')).filter_by(is_deleted=False)
        for user in all_users_query:
            for email in user.all_emails:
                self.all_users_by_email[email] = user

        with patch_default_group_provider(self.default_group_provider):
            self.migrate_event_acls()

    def migrate_event_acls(self):
        self.print_step('migrating event ACLs')
        protection_mode_map = {-1: ProtectionMode.public, 0: ProtectionMode.inheriting, 1: ProtectionMode.protected}
        for legacy_event, event in committing_iterator(self._iter_events(), 5000):
            ac = legacy_event._Conference__ac
            self.print_success('', event_id=event.id)

            old_protection_mode = protection_mode_map[ac._accessProtection]
            if old_protection_mode == ProtectionMode.public and ac.requiredDomains:
                event.protection_mode = ProtectionMode.protected
                self._migrate_domains(event, ac.requiredDomains)
            else:
                event.protection_mode = old_protection_mode

            no_access_contact = convert_to_unicode(getattr(ac, 'contactInfo', ''))
            if no_access_contact != 'no contact info defined':
                event.own_no_access_contact = no_access_contact
            event.access_key = convert_to_unicode(getattr(legacy_event, '_accessKey', ''))
            if not self.quiet:
                self.print_success('Protection mode set to {}'.format(event.protection_mode.name, event_id=event.id))
            for legacy_acl in ac.allowed:
                event_acl = self.convert_acl(legacy_acl)
                if event_acl is None:
                    self.print_warning(cformat('%{red}ACL%{reset}%{yellow} does not exist:%{reset} {}')
                                       .format(legacy_acl), event_id=event.id)
                    continue
                event.update_principal(event_acl, read_access=True, quiet=True)
                if not self.quiet:
                    self.print_msg(cformat('%{green}[{}]%{reset} {}').format('Event ACL', event_acl))

    def _migrate_domains(self, event, old_domains):
        for old_domain in old_domains:
            network = self.domains_map[convert_to_unicode(old_domain.name).lower()]
            event.update_principal(network, read_access=True, quiet=True)
            if not self.quiet:
                self.print_success('Adding {} IPNetworkGroup to the ACLs'.format(network), event_id=event.id)

    def convert_acl(self, old_acl):
        acl = convert_principal(old_acl)
        if (acl is None and old_acl.__class__.__name__ in ('Avatar', 'AvatarUserWrapper') and
                'email' in old_acl.__dict__):
            email = old_acl.__dict__['email'].lower()
            acl = self.all_users_by_email.get(email)
            if acl is not None:
                self.print_warning('Using {} for {} (matched via {})'.format(acl, old_acl, email), always=False)
        return acl

    def _iter_events(self):
        event_it = self.zodb_root['conferences'].itervalues()
        events_query = Event.find(is_deleted=False).order_by(Event.id)
        event_total = len(self.zodb_root['conferences'])
        if self.parallel:
            n, i = self.parallel
            event_it = (e for e in event_it if int(e.id) % n == i)
            event_total = int(ceil(event_total / n))
            events_query = events_query.filter(Event.id % n == i)
        all_events = {ev.id: ev for ev in events_query}
        if self.quiet:
            event_it = verbose_iterator(event_it, event_total, attrgetter('id'), attrgetter('title'))
        for conf in self.flushing_iterator(event_it):
            event = all_events.get(int(conf.id))
            if event is None:
                self.print_error(cformat('%{red!}Event not found in DB'), event_id=conf.id)
                continue
            yield conf, event

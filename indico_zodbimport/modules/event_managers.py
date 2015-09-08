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

from operator import attrgetter

import click

from indico.core.db import db
from indico.modules.events import Event
from indico.modules.events.models.principals import EventPrincipal
from indico.modules.users import User
from indico.util.console import verbose_iterator, cformat
from indico.util.struct.iterables import committing_iterator
from indico_zodbimport import Importer
from indico_zodbimport.util import patch_default_group_provider, convert_principal


class EventManagerImporter(Importer):
    def __init__(self, **kwargs):
        self.default_group_provider = kwargs.pop('default_group_provider')
        super(EventManagerImporter, self).__init__(**kwargs)

    @staticmethod
    def decorate_command(command):
        command = click.option('--default-group-provider', default='legacy-ldap',
                               help="Name of the default group provider")(command)
        return command

    def has_data(self):
        return EventPrincipal.has_rows

    def migrate(self):
        # keep all users in memory to avoid extra queries.
        # the assignment is on purpose to stop the gc from throwing the dict away
        # immediately after retrieving it
        _all_users = User.find_all()
        with patch_default_group_provider(self.default_group_provider):
            with db.session.no_autoflush:
                self.migrate_event_managers()

    def migrate_event_managers(self):
        self.print_step('migrating event managers')
        for event in committing_iterator(self._iter_events(), 5000):
            self.print_success('', event_id=event.id)
            managers = {}
            # add creator as a manager
            creator = event._Conference__creator
            creator_principal = convert_principal(creator)
            if creator_principal is None:
                self.print_warning(cformat('%{yellow!}Creator does not exist: {}').format(creator), event_id=event.id)
            else:
                managers[creator_principal] = EventPrincipal(event_id=event.id, principal=creator_principal,
                                                             full_access=True)
                if not self.quiet:
                    self.print_msg(cformat('    - {} %{green!}[creator]%{reset}').format(creator_principal))
            # add managers
            for manager in event._Conference__ac.managers:
                manager_principal = convert_principal(manager)
                if manager_principal == creator_principal:
                    continue
                elif manager_principal is None:
                    self.print_warning(cformat('%{yellow}Manager does not exist: {}').format(manager),
                                       event_id=event.id)
                    continue
                if manager_principal not in managers:
                    managers[manager_principal] = EventPrincipal(event_id=event.id, principal=manager_principal,
                                                                 full_access=True)
                    if not self.quiet:
                        self.print_msg(cformat('    - {} %{blue!}[manager]%{reset}').format(manager_principal))
            # add registrars
            for registrar in getattr(event, '_Conference__registrars', []):
                registrar_principal = convert_principal(registrar)
                if registrar_principal is None:
                    self.print_warning(cformat('%{yellow!}Registrar does not exist: {}').format(registrar),
                                       event_id=event.id)
                    continue
                elif registrar_principal in managers:
                    managers[registrar_principal].roles = ['registration']
                else:
                    managers[registrar_principal] = EventPrincipal(event_id=event.id, principal=registrar_principal,
                                                                   roles=['registration'])
                if not self.quiet:
                    self.print_msg(cformat('    - {} %{cyan}[registrar]%{reset}').format(registrar_principal))
            db.session.add_all(managers.itervalues())

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

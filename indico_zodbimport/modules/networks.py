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

from ipaddress import ip_network

from indico.core.db import db
from indico.modules.networks.models.networks import IPNetworkGroup
from indico.util.console import cformat
from indico.util.struct.iterables import committing_iterator
from indico_zodbimport import Importer, convert_to_unicode


class NetworkImporter(Importer):
    def has_data(self):
        return IPNetworkGroup.query.has_rows()

    def migrate(self):
        self.migrate_networks()

    def _to_network(self, mask):
        mask = convert_to_unicode(mask).strip()
        net = None
        if re.match(r'^[0-9.]+$', mask):
            # ipv4 mask
            mask = mask.rstrip('.')
            segments = mask.split('.')
            if len(segments) <= 4:
                addr = '.'.join(segments + ['0'] * (4 - len(segments)))
                net = ip_network('{}/{}'.format(addr, 8 * len(segments)))
        elif re.match(r'^[0-9a-f:]+', mask):
            # ipv6 mask
            mask = mask.rstrip(':')  # there shouldn't be a `::` in the IP as it was a startswith-like check before
            segments = mask.split(':')
            if len(segments) <= 8:
                addr = ':'.join(segments + ['0'] * (8 - len(segments)))
                net = ip_network('{}/{}'.format(addr, 16 * len(segments)))
        if net is None:
            self.print_warning(cformat('%{yellow!}Skipped invalid mask: {}').format(mask))
        return net

    def migrate_networks(self):
        self.print_step('migrating networks')
        for domain in committing_iterator(self._iter_domains()):
            ip_networks = filter(None, map(self._to_network, set(domain.filterList)))
            if not ip_networks:
                self.print_warning(cformat('%{yellow}Domain has no valid IPs: {}')
                                   .format(convert_to_unicode(domain.name)))
            network = IPNetworkGroup(name=convert_to_unicode(domain.name),
                                     description=convert_to_unicode(domain.description), networks=ip_networks)
            db.session.add(network)
            self.print_success(repr(network))
        db.session.flush()

    def _iter_domains(self):
        return self.zodb_root['domains'].itervalues()

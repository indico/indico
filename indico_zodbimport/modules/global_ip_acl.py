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
from indico_zodbimport import Importer, convert_to_unicode


class GlobalIPACLImporter(Importer):
    def has_data(self):
        return IPNetworkGroup.query.filter_by(attachment_access_override=True).has_rows()

    def migrate(self):
        self.migrate_global_ip_acl()

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

    def migrate_global_ip_acl(self):
        self.print_step('migrating global ip acl')
        minfo = self.zodb_root['MaKaCInfo']['main']
        ip_networks = filter(None, map(self._to_network, minfo._ip_based_acl_mgr._full_access_acl))
        if not ip_networks:
            self.print_error(cformat('%{red}No valid IPs found'))
            return
        network = IPNetworkGroup(name='Full Attachment Access', hidden=True, attachment_access_override=True,
                                 description='IPs that can access all attachments without authentication',
                                 networks=ip_networks)
        db.session.add(network)
        db.session.flush()
        self.print_success(repr(network), always=True)
        db.session.commit()

# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from flask import has_request_context, request, session
from ipaddress import ip_address
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIPNetwork
from indico.util.string import return_ascii, format_repr


class IPNetworkGroup(db.Model):
    __tablename__ = 'ip_network_groups'

    @declared_attr
    def __table_args__(cls):
        return (db.Index('ix_uq_ip_network_groups_name_lower', db.func.lower(cls.name), unique=True),
                {'schema': 'indico'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    name = db.Column(
        db.String,
        nullable=False
    )
    description = db.Column(
        db.Text,
        nullable=False,
        default=''
    )

    _networks = db.relationship(
        'IPNetwork',
        lazy=False,
        cascade='all, delete-orphan',
        backref=db.backref(
            'group',
            lazy=True
        )
    )
    networks = association_proxy('_networks', 'network', creator=lambda v: IPNetwork(network=v))

    # relationship backrefs:

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'name')

    def __contains__(self, user):
        # This method is called via ``user in principal`` during ACL checks.
        # We have to take the IP from the request so if there's no request
        # (e.g. in the shell) we never grant IP-based access; same if we check
        # for a different user than the one from the current session.
        if not has_request_context() or not request.remote_addr:
            return False
        if session.user != user:
            return False
        return self.contains_ip(request.remote_addr)

    def contains_ip(self, ip):
        ip = ip_address(ip)
        return any(ip in network for network in self.networks)


class IPNetwork(db.Model):
    __tablename__ = 'ip_networks'
    __table_args__ = {'schema': 'indico'}

    group_id = db.Column(
        db.Integer,
        db.ForeignKey('indico.ip_network_groups.id'),
        primary_key=True,
        autoincrement=False
    )
    network = db.Column(
        PyIPNetwork,
        primary_key=True,
        nullable=False
    )

    # relationship backrefs:
    # - group (IPNetworkGroup._networks)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'group_id', 'network')

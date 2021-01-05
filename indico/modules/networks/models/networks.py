# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from ipaddress import ip_address

from flask import has_request_context, request, session
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIPNetwork
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.util.string import format_repr, return_ascii


class IPNetworkGroup(db.Model):
    __tablename__ = 'ip_network_groups'
    principal_type = PrincipalType.network
    principal_order = 1
    is_group = False
    is_network = True
    is_single_person = False
    is_event_role = False
    is_category_role = False
    is_registration_form = False

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
    #: Whether the network group is hidden in ACL forms
    hidden = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Grants all IPs in the network group read access to all attachments
    attachment_access_override = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    _networks = db.relationship(
        'IPNetwork',
        lazy=False,
        cascade='all, delete-orphan',
        collection_class=set,
        backref=db.backref(
            'group',
            lazy=True
        )
    )
    networks = association_proxy('_networks', 'network', creator=lambda v: IPNetwork(network=v))

    # relationship backrefs:
    # - in_category_acls (CategoryPrincipal.ip_network_group)
    # - in_event_acls (EventPrincipal.ip_network_group)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'name', hidden=False, attachment_access_override=False)

    def __contains__(self, user):
        # This method is called via ``user in principal`` during ACL checks.
        # We have to take the IP from the request so if there's no request
        # (e.g. in the shell) we never grant IP-based access; same if we check
        # for a different user than the one from the current session.
        if not has_request_context() or not request.remote_addr:
            return False
        if session.user != user:
            return False
        return self.contains_ip(unicode(request.remote_addr))

    def contains_ip(self, ip):
        ip = ip_address(ip)
        return any(ip in network for network in self.networks)

    @property
    def locator(self):
        return {'network_group_id': self.id}


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

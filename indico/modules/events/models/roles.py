# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii


class EventRole(db.Model):
    __tablename__ = 'roles'
    __table_args__ = (db.CheckConstraint('code = upper(code)', 'uppercase_code'),
                      db.Index(None, 'event_id', 'code', unique=True),
                      {'schema': 'events'})

    is_group = False
    is_event_role = True
    is_category_role = False
    is_single_person = True
    is_network = False
    is_registration_form = False
    principal_order = 2
    principal_type = PrincipalType.event_role

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        nullable=False,
        index=True
    )
    name = db.Column(
        db.String,
        nullable=False
    )
    code = db.Column(
        db.String,
        nullable=False
    )
    color = db.Column(
        db.String,
        nullable=False
    )

    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'roles',
            cascade='all, delete-orphan',
            lazy=True
        )
    )
    members = db.relationship(
        'User',
        secondary='events.role_members',
        lazy=True,
        collection_class=set,
        backref=db.backref('event_roles', lazy=True, collection_class=set),
    )

    # relationship backrefs:
    # - in_attachment_acls (AttachmentPrincipal.event_role)
    # - in_attachment_folder_acls (AttachmentFolderPrincipal.event_role)
    # - in_contribution_acls (ContributionPrincipal.event_role)
    # - in_event_acls (EventPrincipal.event_role)
    # - in_event_settings_acls (EventSettingPrincipal.event_role)
    # - in_session_acls (SessionPrincipal.event_role)
    # - in_track_acls (TrackPrincipal.event_role)

    def __contains__(self, user):
        return user is not None and self in user.event_roles

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'code', _text=self.name)

    @locator_property
    def locator(self):
        return dict(self.event.locator, role_id=self.id)

    @property
    def identifier(self):
        return 'EventRole:{}'.format(self.id)

    @property
    def css(self):
        return 'color: #{0} !important; border-color: #{0} !important'.format(self.color)

    @property
    def style(self):
        return {'color': '#' + self.color, 'borderColor': '#' + self.color}


role_members_table = db.Table(
    'role_members',
    db.metadata,
    db.Column(
        'role_id',
        db.Integer,
        db.ForeignKey('events.roles.id'),
        primary_key=True,
        nullable=False,
        index=True
    ),
    db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('users.users.id'),
        primary_key=True,
        nullable=False,
        index=True
    ),
    schema='events'
)

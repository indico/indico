# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_method

from indico.core.db import db
from indico.core.db.sqlalchemy.custom.utcdatetime import UTCDateTime
from indico.modules.rb.models.blocking_principals import BlockingPrincipal
from indico.modules.rb.util import rb_is_admin
from indico.util.date_time import now_utc
from indico.util.string import format_repr, return_ascii
from indico.util.user import iter_acl
from indico.web.flask.util import url_for


class Blocking(db.Model):
    __tablename__ = 'blockings'
    __table_args__ = {'schema': 'roombooking'}

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    created_by_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=False
    )
    created_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )
    start_date = db.Column(
        db.Date,
        nullable=False,
        index=True
    )
    end_date = db.Column(
        db.Date,
        nullable=False,
        index=True
    )
    reason = db.Column(
        db.Text,
        nullable=False
    )

    _allowed = db.relationship(
        'BlockingPrincipal',
        backref='blocking',
        cascade='all, delete-orphan',
        collection_class=set
    )
    allowed = association_proxy('_allowed', 'principal', creator=lambda v: BlockingPrincipal(principal=v))
    blocked_rooms = db.relationship(
        'BlockedRoom',
        backref='blocking',
        cascade='all, delete-orphan'
    )
    #: The user who created this blocking.
    created_by_user = db.relationship(
        'User',
        lazy=False,
        backref=db.backref(
            'blockings',
            lazy='dynamic'
        )
    )

    @hybrid_method
    def is_active_at(self, d):
        return self.start_date <= d <= self.end_date

    @is_active_at.expression
    def is_active_at(self, d):
        return (self.start_date <= d) & (d <= self.end_date)

    def can_edit(self, user, allow_admin=True):
        if not user:
            return False
        return user == self.created_by_user or (allow_admin and rb_is_admin(user))

    def can_delete(self, user, allow_admin=True):
        if not user:
            return False
        return user == self.created_by_user or (allow_admin and rb_is_admin(user))

    def can_override(self, user, room=None, explicit_only=False, allow_admin=True):
        """Check if a user can override the blocking.

        The following persons are authorized to override a blocking:
        - the creator of the blocking
        - anyone on the blocking's ACL
        - unless explicit_only is set: rb admins and room managers (if a room is given)
        """
        if not user:
            return False
        if self.created_by_user == user:
            return True
        if not explicit_only:
            if allow_admin and rb_is_admin(user):
                return True
            if room and room.can_manage(user, allow_admin=allow_admin):
                return True
        return any(user in principal for principal in iter_acl(self.allowed))

    @property
    def external_details_url(self):
        return url_for('rb.blocking_link', blocking_id=self.id, _external=True)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'start_date', 'end_date', _text=self.reason)

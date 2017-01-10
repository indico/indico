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

from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_method

from indico.core.db import db
from indico.core.db.sqlalchemy.custom.utcdatetime import UTCDateTime
from indico.modules.rb.models.blocking_principals import BlockingPrincipal
from indico.modules.rb.util import rb_is_admin
from indico.util.date_time import now_utc
from indico.util.string import return_ascii
from indico.util.user import iter_acl


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

    def can_be_modified(self, user):
        """
        The following persons are authorized to modify a blocking:
        - owner (the one who created the blocking)
        - admin (of course)
        """
        return user and (user == self.created_by_user or rb_is_admin(user))

    def can_be_deleted(self, user):
        return self.can_be_modified(user)

    def can_be_overridden(self, user, room=None, explicit_only=False):
        """Determines if a user can override the blocking

        The following persons are authorized to override a blocking:
        - owner (the one who created the blocking)
        - any users on the blocking's ACL
        - unless explicitOnly is set: admins and room owners (if a room is given)
        """
        if not user:
            return False
        if self.created_by_user == user:
            return True
        if not explicit_only:
            if rb_is_admin(user):
                return True
            elif room and room.is_owned_by(user):
                return True
        return any(user in principal for principal in iter_acl(self.allowed))

    @return_ascii
    def __repr__(self):
        return '<Blocking({0}, {1}, {2}, {3}, {4})>'.format(
            self.id,
            self.created_by_user,
            self.reason,
            self.start_date,
            self.end_date
        )

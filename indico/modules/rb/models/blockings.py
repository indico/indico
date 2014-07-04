# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

"""
Schema of a blocking (dates, related rooms and principals)
"""


from sqlalchemy.ext.hybrid import hybrid_method

from indico.core.db import db
from indico.core.db.sqlalchemy.custom.utcdatetime import UTCDateTime
from indico.util.date_time import now_utc
from indico.util.string import return_ascii
from MaKaC.user import AvatarHolder


class Blocking(db.Model):
    __tablename__ = 'blockings'

    # columns

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    created_by = db.Column(
        db.String,
        nullable=False
    )
    created_at = db.Column(
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

    # relationships

    allowed = db.relationship(
        'BlockingPrincipal',
        backref='blocking',
        cascade='all, delete-orphan'
    )
    blocked_rooms = db.relationship(
        'BlockedRoom',
        backref='blocking',
        cascade='all, delete-orphan'
    )

    @hybrid_method
    def is_active_at(self, d):
        return (self.start_date <= d) & (d <= self.end_date)

    @property
    def created_by_user(self):
        return AvatarHolder().getById(self.created_by)

    @created_by_user.setter
    def created_by_user(self, user):
        self.created_by = user.getId()

    def can_be_modified(self, user):
        """
        The following persons are authorized to modify a blocking:
        - owner (the one who created the blocking)
        - admin (of course)
        """
        if not user:
            return False
        return user == self.created_by_user or user.isAdmin()

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
            if user.isAdmin():
                return True
            elif room and room.is_owned_by(user):
                return True
        for principal in self.allowed:
            if principal.entity.containsUser(user):
                return True
        return False

    @return_ascii
    def __repr__(self):
        return u'<Blocking({0}, {1}, {2}, {3}, {4})>'.format(
            self.id,
            self.created_by,
            self.reason,
            self.start_date,
            self.end_date
        )

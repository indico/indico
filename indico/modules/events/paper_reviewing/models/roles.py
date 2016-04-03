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


from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.util.i18n import _
from indico.util.string import format_repr, return_ascii
from indico.util.struct.enum import TitledIntEnum


class PaperReviewingRoleType(TitledIntEnum):
    __titles__ = (_('Reviewer'), _('Referee'), _('Editor'))
    reviewer = 0
    referee = 1
    editor = 2


class PaperReviewingRole(db.Model):
    """Represents a role a user performs regarding a particular contribution."""

    __tablename__ = 'contribution_roles'
    __table_args__ = {'schema': 'event_paper_reviewing'}

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        nullable=False,
        index=True
    )
    contribution_id = db.Column(
        db.Integer,
        db.ForeignKey('events.contributions.id'),
        index=True,
        nullable=False
    )
    role = db.Column(
        PyIntEnum(PaperReviewingRoleType),
        nullable=False,
        index=True
    )
    contribution = db.relationship(
        'Contribution',
        lazy=False,
        backref=db.backref(
            'paper_reviewing_roles',
            lazy=True
        )
    )
    user = db.relationship(
        'User',
        lazy=False,
        backref=db.backref(
            'paper_reviewing_roles',
            lazy='dynamic'
        )
    )

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', user_id=self.user_id, contribution_id=self.contribution_id)

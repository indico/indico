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

from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import get_model_by_table_name


def _get_next_position(context):
    """Get the next abstracts template position for the event."""
    event_id = context.current_parameters['event_id']
    cls = get_model_by_table_name(context.compiled.statement.table.fullname)
    res = db.session.query(db.func.max(cls.position)).filter_by(event_id=event_id).one()
    return (res[0] or 0) + 1


class NotificationTemplateBase(db.Model):
    """Base class for notification templates."""

    __abstract__ = True

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String,
        nullable=False
    )

    @declared_attr
    def event_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey('events.events.id'),
            index=True,
            nullable=False
        )

    @declared_attr
    def reply_to_address(cls):
        """The address to use as Reply-To in the notification email"""
        return db.Column(
            db.String,
            nullable=False
        )

    @declared_attr
    def subject(cls):
        """The subject of the notification email"""
        return db.Column(
            db.String,
            nullable=False
        )

    @declared_attr
    def body(cls):
        """The body of the notification template"""
        return db.Column(
            db.Text,
            nullable=False,
            default=''
        )

    @declared_attr
    def position(cls):
        """The relative position of the template in the list of templates"""
        return db.Column(
            db.Integer,
            nullable=False,
            default=_get_next_position
        )

    @declared_attr
    def stop_on_match(cls):
        """Whether to stop checking the rest of the conditions when a match is found"""
        return db.Column(
            db.Boolean,
            nullable=False,
            default=True
        )

    @declared_attr
    def conditions(cls):
        """Conditions need to be met to send the notification email"""
        return db.Column(
            JSON,
            nullable=False
        )

    @declared_attr
    def extra_cc_emails(cls):
        """List of extra email addresses to be added as CC in the notification email"""
        return db.Column(
            ARRAY(db.String),
            nullable=False,
            default=[],
        )

    @declared_attr
    def event_new(cls):
        return db.relationship(
            'Event',
            lazy=True,
            backref=db.backref(
                cls.events_backref_name,
                lazy='dynamic'
            )
        )

    @property
    def to_emails(self):
        """List of email addresses to send the notification email"""
        raise NotImplementedError

    @property
    def cc_emails(self):
        """List of email addresses to be added as CC in the notification email"""
        return set(self.extra_cc_emails)

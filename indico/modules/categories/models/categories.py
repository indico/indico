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

import pytz
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.attachments import AttachedItemsMixin
from indico.core.db.sqlalchemy.descriptions import DescriptionMixin
from indico.core.db.sqlalchemy.protection import ProtectionManagersMixin, ProtectionMode
from indico.core.db.sqlalchemy.searchable_titles import SearchableTitleMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.util.decorators import strict_classproperty
from indico.util.i18n import _
from indico.util.locators import locator_property
from indico.util.string import RichMarkup, text_to_repr, format_repr, return_ascii
from indico.util.struct.enum import TitledIntEnum


def _get_next_position(context):
    parent_id = context.current_parameters['parent_id']
    res = db.session.query(db.func.max(Category.position)).filter_by(parent_id=parent_id).one()
    return (res[0] or 0) + 1


class EventMessageMode(TitledIntEnum):
    __titles__ = [_('None'), _('Info'), _('Warning'), _('Danger')]
    disabled = 0
    info = 1
    warning = 2
    danger = 3


class Category(SearchableTitleMixin, DescriptionMixin, ProtectionManagersMixin, AttachedItemsMixin, db.Model):
    """An Indico category"""

    __tablename__ = 'categories'
    disallowed_protection_modes = frozenset()
    inheriting_have_acl = True
    description_wrapper = RichMarkup
    ATTACHMENT_FOLDER_ID_COLUMN = 'category_id'

    @strict_classproperty
    @classmethod
    def __auto_table_args(cls):
        return (db.CheckConstraint("(icon IS NULL) = (icon_metadata::text = 'null')", 'valid_icon'),
                db.CheckConstraint("(parent_id IS NULL) = (id = 0)", 'valid_parent'),
                db.CheckConstraint("(id != 0) OR (protection_mode != {})".format(ProtectionMode.inheriting),
                                   'root_not_inheriting'),
                {'schema': 'categories'})

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    parent_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.categories.id'),
        index=True,
        nullable=True
    )
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    position = db.Column(
        db.Integer,
        nullable=False,
        default=_get_next_position
    )
    visibility = db.Column(
        db.Integer,
        nullable=True,
        default=None
    )
    icon_metadata = db.Column(
        JSON,
        nullable=False,
        default=None
    )
    icon = db.deferred(db.Column(
        db.LargeBinary,
        nullable=True
    ))
    timezone = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    default_event_themes = db.Column(
        JSON,
        nullable=False,
        default={}
    )
    event_creation_restricted = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    event_creation_notification_emails = db.Column(
        ARRAY(db.String),
        nullable=False,
        default=[]
    )
    event_message_mode = db.Column(
        PyIntEnum(EventMessageMode),
        nullable=False,
        default=EventMessageMode.disabled
    )
    event_message = db.Column(
        db.Text,
        nullable=False,
        default=''
    )

    children = db.relationship(
        'Category',
        order_by='Category.position',
        primaryjoin=(id == db.remote(parent_id)) & ~db.remote(is_deleted),
        lazy=True,
        backref=db.backref(
            'parent',
            primaryjoin=(db.remote(id) == parent_id),
            lazy=True
        )
    )

    # relationship backrefs:
    # - parent (Category.children)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', is_deleted=False, _text=text_to_repr(self.title, max_length=75))

    @property
    def protection_parent(self):
        return self.parent if not self.is_root else None

    @locator_property
    def locator(self):
        return {'categId': self.id}

    @hybrid_property
    def is_root(self):
        return self.parent_id is None

    @is_root.expression
    def is_root(cls):
        return cls.parent_id.is_(None)

    @property
    def tzinfo(self):
        return pytz.timezone(self.timezone)


Category.register_protection_events()

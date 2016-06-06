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
from sqlalchemy.sql import select, literal

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.attachments import AttachedItemsMixin
from indico.core.db.sqlalchemy.descriptions import DescriptionMixin
from indico.core.db.sqlalchemy.protection import ProtectionManagersMixin, ProtectionMode
from indico.core.db.sqlalchemy.searchable_titles import SearchableTitleMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.util.caching import memoize_request
from indico.util.decorators import strict_classproperty
from indico.util.i18n import _
from indico.util.locators import locator_property
from indico.util.string import RichMarkup, text_to_repr, format_repr, return_ascii
from indico.util.struct.enum import TitledIntEnum
from indico.web.flask.util import url_for


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
    no_access_contact = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    suggestions_disabled = db.Column(
        db.Boolean,
        nullable=False,
        default=False
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
    acl_entries = db.relationship(
        'CategoryPrincipal',
        backref='category',
        cascade='all, delete-orphan',
        collection_class=set
    )

    # relationship backrefs:
    # - attachment_folders (AttachmentFolder.category)
    # - events (Event.category)
    # - favorite_of (User.favorite_categories)
    # - legacy_mapping (LegacyCategoryMapping.category)
    # - parent (Category.children)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', is_deleted=False, _text=text_to_repr(self.title, max_length=75))

    @property
    def protection_parent(self):
        return self.parent if not self.is_root else None

    @locator_property
    def locator(self):
        return {'category_id': self.id}

    @classmethod
    def get_root(cls):
        """Get the root category or create if if needed"""
        root = cls.query.filter(cls.is_root).one_or_none()
        if not root:
            root = cls(id=0, title='Home', protection_mode=ProtectionMode.public)
            db.session.add(root)
        return root

    @property
    def url(self):
        if self.is_root:
            return url_for('misc.index')
        else:
            return url_for('category.categoryDisplay', self)

    @hybrid_property
    def is_root(self):
        return self.parent_id is None

    @is_root.expression
    def is_root(cls):
        return cls.parent_id.is_(None)

    @property
    def tzinfo(self):
        return pytz.timezone(self.timezone)

    def can_create_events(self, user):
        """Check whether the user can create events in the category."""
        return user and (not self.event_creation_restricted or self.can_manage(user, role='create'))

    def _get_chain_query(self, start_criterion):
        cte_query = (select([Category.id, Category.parent_id, literal(0).label('level')])
                     .where(start_criterion)
                     .cte('category_chain', recursive=True))
        parent_query = (select([Category.id, Category.parent_id, cte_query.c.level + 1])
                        .where(Category.id == cte_query.c.parent_id))
        cte_query = cte_query.union_all(parent_query)
        return Category.query.join(cte_query, Category.id == cte_query.c.id).order_by(cte_query.c.level.desc())

    @property
    def chain_query(self):
        """Get a query object for the category chain.

        The query retrieves the root category first and then all the
        intermediate categories up to (and including) this category.
        """
        return self._get_chain_query(Category.id == self.id)

    @property
    def parent_chain_query(self):
        """Get a query object for the category's parent chain.

        The query retrieves the root category first and then all the
        intermediate categories up to (excluding) this category.
        """
        return self._get_chain_query(Category.id == self.parent_id)

    @memoize_request
    def get_chain_titles(self):
        """Retrieve the category titles from the root to the category"""
        return [c.title for c in self.chain_query]


Category.register_protection_events()

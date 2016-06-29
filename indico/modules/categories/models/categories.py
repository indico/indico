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
from sqlalchemy import orm, DDL
from sqlalchemy.dialects.postgresql import ARRAY, array, JSON
from sqlalchemy.event import listens_for
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import column_property
from sqlalchemy.sql import select, literal

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
from indico.util.string import MarkdownText, RichMarkup, text_to_repr, format_repr, return_ascii
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
    allow_no_access_contact = True
    ATTACHMENT_FOLDER_ID_COLUMN = 'category_id'

    @strict_classproperty
    @classmethod
    def __auto_table_args(cls):
        return (db.CheckConstraint("(icon IS NULL) = (icon_metadata::text = 'null')", 'valid_icon'),
                db.CheckConstraint("(logo IS NULL) = (logo_metadata::text = 'null')", 'valid_logo'),
                db.CheckConstraint("(parent_id IS NULL) = (id = 0)", 'valid_parent'),
                db.CheckConstraint("(id != 0) OR NOT is_deleted", 'root_not_deleted'),
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
    logo_metadata = db.Column(
        JSON,
        nullable=False,
        default=None
    )
    logo = db.deferred(db.Column(
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
    _event_message = db.Column(
        'event_message',
        db.Text,
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

    # column properties:
    # - deep_events_count

    # relationship backrefs:
    # - attachment_folders (AttachmentFolder.category)
    # - events (Event.category)
    # - favorite_of (User.favorite_categories)
    # - legacy_mapping (LegacyCategoryMapping.category)
    # - parent (Category.children)

    @hybrid_property
    def event_message(self):
        return MarkdownText(self._event_message)

    @event_message.setter
    def event_message(self, value):
        self._event_message = value

    @event_message.expression
    def event_message(cls):
        return cls._event_message

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
            # XXX: change this when adapting the display pages
            return url_for('category.categoryDisplay', categId=self.id)

    @hybrid_property
    def is_root(self):
        return self.parent_id is None

    @is_root.expression
    def is_root(cls):
        return cls.parent_id.is_(None)

    @property
    def is_empty(self):
        return not self.deep_children_count and not self.deep_events_count

    @property
    def has_icon(self):
        return self.icon_metadata is not None

    @property
    def has_logo(self):
        return self.logo_metadata is not None

    @property
    def tzinfo(self):
        return pytz.timezone(self.timezone)

    def can_create_events(self, user):
        """Check whether the user can create events in the category."""
        # if creation is not restricted anyone who can access the category
        # can also create events in it, otherwise only people with the
        # creation role can
        return user and ((not self.event_creation_restricted and self.can_access(user)) or
                         self.can_manage(user, role='create'))

    def move(self, target):
        """Move the category into another category."""
        assert not self.is_root
        self.position = (max(x.position for x in target.children) + 1) if target.children else 1
        self.parent = target
        db.session.flush()
        # TODO: trigger category moved signal

    @classmethod
    def get_tree_cte(cls, col='id'):
        """Create a CTE for the category tree.

        The CTE contains the followign columns:
        - ``id`` -- the category id
        - ``path`` -- an array containing the path from the root to
                      the category itself
        - ``is_deleted`` -- whether the category is deleted

        :param col: The name of the column to use in the path
        """
        cat_alias = db.aliased(cls)
        path_column = getattr(cat_alias, col)
        cte_query = (select([cat_alias.id, array([path_column]).label('path'), cat_alias.is_deleted])
                     .where(cat_alias.parent_id.is_(None))
                     .cte(recursive=True))
        rec_query = (select([cat_alias.id,
                             cte_query.c.path.op('||')(path_column),
                             cte_query.c.is_deleted | cat_alias.is_deleted])
                     .where(cat_alias.parent_id == cte_query.c.id))
        cte_query = cte_query.union_all(rec_query)
        return cte_query

    @property
    def deep_children_query(self):
        """Get a query object for all subcategories.

        This includes subcategories at any level of nesting.
        """
        cte = Category.get_tree_cte()
        return (Category.query
                .join(cte, Category.id == cte.c.id)
                .filter(cte.c.path.contains([self.id]),
                        cte.c.id != self.id,
                        ~cte.c.is_deleted))

    @staticmethod
    def _get_chain_query(start_criterion):
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

    @property
    def icon_url(self):
        """Get the HTTP URL of the icon."""
        return url_for('categories.display_icon', self, slug=self.icon_metadata['hash'])

    @property
    def logo_url(self):
        """Get the HTTP URL of the logo."""
        return url_for('categories.display_logo', self, slug=self.logo_metadata['hash'])


Category.register_protection_events()


@listens_for(orm.mapper, 'after_configured', once=True)
def _mappers_configured():
    # We create some column properties here since even with `declared_attr`
    # the code runs at import time, making it impossible/risky to import other
    # modules or reference the object itself in there.
    # The advantage of those column properties is that they behave like regular
    # (read-only) columns even though they are generated by subqueries.  This
    # allows them to be loaded together with the test of the data, avoiding
    # extra queries.  To load them automatically you need to undefer them using
    # the `undefer` query option, e.g. `.options(undefer('chain_titles'))`.

    from indico.modules.events import Event

    # Category.chain_titles -- a list of the titles in the parent chain,
    # starting with the root category down to the current category.
    cte = Category.get_tree_cte('title')
    query = select([cte.c.path]).where(cte.c.id == Category.id).correlate_except(cte)
    Category.chain_titles = column_property(query, deferred=True)

    # Category.deep_events_count -- the number of events in the category
    # or any child category (excluding deleted events)
    cte = Category.get_tree_cte()
    crit = db.and_(cte.c.id == Event.category_id,
                   cte.c.path.contains(array([Category.id])),
                   ~cte.c.is_deleted,
                   ~Event.is_deleted)
    query = select([db.func.count()]).where(crit).correlate_except(Event)
    Category.deep_events_count = column_property(query, deferred=True)

    # Category.deep_children_count -- the number of subcategories in the
    # category or any child category (excluding deleted ones)
    cte = Category.get_tree_cte()
    crit = db.and_(cte.c.path.contains(array([Category.id])),
                   cte.c.id != Category.id, ~cte.c.is_deleted)
    query = select([db.func.count()]).where(crit).correlate_except(cte)
    Category.deep_children_count = column_property(query, deferred=True)


@listens_for(Category.__table__, 'after_create')
def _add_deletion_consistency_trigger(target, conn, **kw):
    sql = """
        CREATE CONSTRAINT TRIGGER consistent_deleted
        AFTER INSERT OR UPDATE OF parent_id, is_deleted
        ON {table}
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE categories.check_consistency_deleted();
    """.format(table=target.fullname)
    DDL(sql).execute(conn)


@listens_for(Category.__table__, 'after_create')
def _add_cycle_check_trigger(target, conn, **kw):
    sql = """
        CREATE CONSTRAINT TRIGGER no_cycles
        AFTER INSERT OR UPDATE OF parent_id
        ON {table}
        NOT DEFERRABLE
        FOR EACH ROW
        EXECUTE PROCEDURE categories.check_cycles();
    """.format(table=target.fullname)
    DDL(sql).execute(conn)

# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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
from sqlalchemy import DDL, orm
from sqlalchemy.dialects.postgresql import ARRAY, JSON, array
from sqlalchemy.event import listens_for
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import column_property
from sqlalchemy.sql import exists, func, literal, select

from indico.core import signals
from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.attachments import AttachedItemsMixin
from indico.core.db.sqlalchemy.descriptions import DescriptionMixin, RenderMode
from indico.core.db.sqlalchemy.protection import ProtectionManagersMixin, ProtectionMode
from indico.core.db.sqlalchemy.searchable_titles import SearchableTitleMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.util.date_time import get_display_tz
from indico.util.decorators import strict_classproperty
from indico.util.i18n import _
from indico.util.locators import locator_property
from indico.util.string import MarkdownText, format_repr, return_ascii, text_to_repr
from indico.util.struct.enum import RichIntEnum
from indico.web.flask.util import url_for


def _get_next_position(context):
    parent_id = context.current_parameters['parent_id']
    res = db.session.query(db.func.max(Category.position)).filter_by(parent_id=parent_id).one()
    return (res[0] or 0) + 1


def _get_default_event_themes():
    from indico.modules.events.layout import theme_settings
    return {
        'meeting': theme_settings.defaults['meeting'],
        'lecture': theme_settings.defaults['lecture']
    }


class EventMessageMode(RichIntEnum):
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
    possible_render_modes = {RenderMode.markdown}
    default_render_mode = RenderMode.markdown
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
                db.CheckConstraint('visibility IS NULL OR visibility > 0', 'valid_visibility'),
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
        default=lambda: None
    )
    icon = db.deferred(db.Column(
        db.LargeBinary,
        nullable=True
    ))
    logo_metadata = db.Column(
        JSON,
        nullable=False,
        default=lambda: None
    )
    logo = db.deferred(db.Column(
        db.LargeBinary,
        nullable=True
    ))
    timezone = db.Column(
        db.String,
        nullable=False,
        default=lambda: config.DEFAULT_TIMEZONE
    )
    default_event_themes = db.Column(
        JSON,
        nullable=False,
        default=_get_default_event_themes
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
    notify_managers = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    default_ticket_template_id = db.Column(
        db.ForeignKey('indico.designer_templates.id'),
        nullable=True,
        index=True
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
    default_ticket_template = db.relationship(
        'DesignerTemplate',
        lazy=True,
        foreign_keys=default_ticket_template_id,
        backref='default_ticket_template_of'
    )

    # column properties:
    # - deep_events_count

    # relationship backrefs:
    # - attachment_folders (AttachmentFolder.category)
    # - designer_templates (DesignerTemplate.category)
    # - events (Event.category)
    # - favorite_of (User.favorite_categories)
    # - legacy_mapping (LegacyCategoryMapping.category)
    # - parent (Category.children)
    # - settings (CategorySetting.category)
    # - suggestions (SuggestedCategory.category)

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
        """Get the root category"""
        return cls.query.filter(cls.is_root).one()

    @property
    def url(self):
        return url_for('categories.display', self)

    @property
    def has_only_events(self):
        return self.has_events and not self.children

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
    def has_effective_icon(self):
        return self.effective_icon_data['metadata'] is not None

    @property
    def has_logo(self):
        return self.logo_metadata is not None

    @property
    def tzinfo(self):
        return pytz.timezone(self.timezone)

    @property
    def display_tzinfo(self):
        """The tzinfo of the category or the one specified by the user"""
        return get_display_tz(self, as_timezone=True)

    def can_create_events(self, user):
        """Check whether the user can create events in the category."""
        # if creation is not restricted anyone who can access the category
        # can also create events in it, otherwise only people with the
        # creation role can
        return user and ((not self.event_creation_restricted and self.can_access(user)) or
                         self.can_manage(user, permission='create'))

    def move(self, target):
        """Move the category into another category."""
        assert not self.is_root
        old_parent = self.parent
        self.position = (max(x.position for x in target.children) + 1) if target.children else 1
        self.parent = target
        db.session.flush()
        signals.category.moved.send(self, old_parent=old_parent)

    @classmethod
    def get_tree_cte(cls, col='id'):
        """Create a CTE for the category tree.

        The CTE contains the following columns:

        - ``id`` -- the category id
        - ``path`` -- an array containing the path from the root to
                      the category itself
        - ``is_deleted`` -- whether the category is deleted

        :param col: The name of the column to use in the path or a
                    callable receiving the category alias that must
                    return the expression used for the 'path'
                    retrieved by the CTE.
        """
        cat_alias = db.aliased(cls)
        if callable(col):
            path_column = col(cat_alias)
        else:
            path_column = getattr(cat_alias, col)
        cte_query = (select([cat_alias.id, array([path_column]).label('path'), cat_alias.is_deleted])
                     .where(cat_alias.parent_id.is_(None))
                     .cte(recursive=True))
        rec_query = (select([cat_alias.id,
                             cte_query.c.path.op('||')(path_column),
                             cte_query.c.is_deleted | cat_alias.is_deleted])
                     .where(cat_alias.parent_id == cte_query.c.id))
        return cte_query.union_all(rec_query)

    @classmethod
    def get_protection_cte(cls):
        cat_alias = db.aliased(cls)
        cte_query = (select([cat_alias.id, cat_alias.protection_mode])
                     .where(cat_alias.parent_id.is_(None))
                     .cte(recursive=True))
        rec_query = (select([cat_alias.id,
                             db.case({ProtectionMode.inheriting.value: cte_query.c.protection_mode},
                                     else_=cat_alias.protection_mode, value=cat_alias.protection_mode)])
                     .where(cat_alias.parent_id == cte_query.c.id))
        return cte_query.union_all(rec_query)

    def get_protection_parent_cte(self):
        cte_query = (select([Category.id, db.cast(literal(None), db.Integer).label('protection_parent')])
                     .where(Category.id == self.id)
                     .cte(recursive=True))
        rec_query = (select([Category.id,
                             db.case({ProtectionMode.inheriting.value: func.coalesce(cte_query.c.protection_parent,
                                                                                     self.id)},
                                     else_=Category.id, value=Category.protection_mode)])
                     .where(Category.parent_id == cte_query.c.id))
        return cte_query.union_all(rec_query)

    @classmethod
    def get_icon_data_cte(cls):
        cat_alias = db.aliased(cls)
        cte_query = (select([cat_alias.id, cat_alias.id.label('source_id'), cat_alias.icon_metadata])
                     .where(cat_alias.parent_id.is_(None))
                     .cte(recursive=True))
        rec_query = (select([cat_alias.id,
                             db.case({'null': cte_query.c.source_id}, else_=cat_alias.id,
                                     value=db.func.json_typeof(cat_alias.icon_metadata)),
                             db.case({'null': cte_query.c.icon_metadata}, else_=cat_alias.icon_metadata,
                                     value=db.func.json_typeof(cat_alias.icon_metadata))])
                     .where(cat_alias.parent_id == cte_query.c.id))
        return cte_query.union_all(rec_query)

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

    def nth_parent(self, n_categs, fail_on_overflow=True):
        """Return the nth parent of the category.

        :param n_categs: the number of categories to go up
        :param fail_on_overflow: whether to fail if we try to go above the root category
        :return: `Category` object or None (only if ``fail_on_overflow`` is not set)
        """
        if n_categs == 0:
            return self
        chain = self.parent_chain_query.all()

        assert n_categs >= 0
        if n_categs > len(chain):
            if fail_on_overflow:
                raise IndexError("Root category has no parent!")
            else:
                return None
        return chain[::-1][n_categs - 1]

    def is_descendant_of(self, categ):
        return categ != self and self.parent_chain_query.filter(Category.id == categ.id).has_rows()

    @property
    def visibility_horizon_query(self):
        """Get a query object that returns the highest category this one is visible from."""
        cte_query = (select([Category.id, Category.parent_id,
                             db.case([(Category.visibility.is_(None), None)],
                                     else_=(Category.visibility - 1)).label('n'),
                             literal(0).label('level')])
                     .where(Category.id == self.id)
                     .cte('visibility_horizon', recursive=True))
        parent_query = (select([Category.id, Category.parent_id,
                                db.case([(Category.visibility.is_(None) & cte_query.c.n.is_(None), None)],
                                        else_=db.func.least(Category.visibility, cte_query.c.n) - 1),
                                cte_query.c.level + 1])
                        .where(db.and_(Category.id == cte_query.c.parent_id,
                                       (cte_query.c.n > 0) | cte_query.c.n.is_(None))))
        cte_query = cte_query.union_all(parent_query)
        return db.session.query(cte_query.c.id, cte_query.c.n).order_by(cte_query.c.level.desc()).limit(1)

    @property
    def own_visibility_horizon(self):
        """Get the highest category this one would like to be visible from (configured visibility)."""
        if self.visibility is None:
            return Category.get_root()
        else:
            return self.nth_parent(self.visibility - 1)

    @property
    def real_visibility_horizon(self):
        """Get the highest category this one is actually visible from (as limited by categories above)."""
        horizon_id, final_visibility = self.visibility_horizon_query.one()
        if final_visibility is not None and final_visibility < 0:
            return None  # Category is invisible
        return Category.get(horizon_id)

    @property
    def visible_categories_cte(self):
        """
        Get a sqlalchemy select for the visible categories within
        this category, including the category itself.
        """
        cte_query = (select([Category.id, literal(0).label('level')])
                     .where((Category.id == self.id) & (Category.visibility.is_(None) | (Category.visibility > 0)))
                     .cte('visibility_chain', recursive=True))
        parent_query = (select([Category.id, cte_query.c.level + 1])
                        .where(db.and_(Category.parent_id == cte_query.c.id,
                                       db.or_(Category.visibility.is_(None),
                                              Category.visibility > cte_query.c.level + 1))))
        return cte_query.union_all(parent_query)

    @property
    def visible_categories_query(self):
        """
        Get a query object for the visible categories within
        this category, including the category itself.
        """
        cte_query = self.visible_categories_cte
        return Category.query.join(cte_query, Category.id == cte_query.c.id)

    @property
    def icon_url(self):
        """Get the HTTP URL of the icon."""
        return url_for('categories.display_icon', self, slug=self.icon_metadata['hash'])

    @property
    def effective_icon_url(self):
        """Get the HTTP URL of the icon (possibly inherited)."""
        data = self.effective_icon_data
        return url_for('categories.display_icon', category_id=data['source_id'], slug=data['metadata']['hash'])

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
    # allows them to be loaded together with the rest of the data, avoiding
    # extra queries.  To load them automatically you need to undefer them using
    # the `undefer` query option, e.g. `.options(undefer('chain_titles'))`.

    from indico.modules.events import Event

    # Category.effective_protection_mode -- the effective protection mode
    # (public/protected) of the category, even if it's inheriting it from its
    # parent category
    cte = Category.get_protection_cte()
    query = select([cte.c.protection_mode]).where(cte.c.id == Category.id).correlate_except(cte)
    Category.effective_protection_mode = column_property(query, deferred=True, expire_on_flush=False)

    # Category.effective_icon_data -- the effective icon data of the category,
    # either set on the category itself or inherited from it
    cte = Category.get_icon_data_cte()
    query = (select([db.func.json_build_object('source_id', cte.c.source_id,
                                               'metadata', cte.c.icon_metadata)])
             .where(cte.c.id == Category.id)
             .correlate_except(cte))
    Category.effective_icon_data = column_property(query, deferred=True)

    # Category.event_count -- the number of events in the category itself,
    # excluding deleted events
    query = (select([db.func.count(Event.id)])
             .where((Event.category_id == Category.id) & ~Event.is_deleted)
             .correlate_except(Event))
    Category.event_count = column_property(query, deferred=True)

    # Category.has_events -- whether the category itself contains any
    # events, excluding deleted events
    query = (exists([1])
             .where((Event.category_id == Category.id) & ~Event.is_deleted)
             .correlate_except(Event))
    Category.has_events = column_property(query, deferred=True)

    # Category.chain_titles -- a list of the titles in the parent chain,
    # starting with the root category down to the current category.
    cte = Category.get_tree_cte('title')
    query = select([cte.c.path]).where(cte.c.id == Category.id).correlate_except(cte)
    Category.chain_titles = column_property(query, deferred=True)

    # Category.chain -- a list of the ids and titles in the parent
    # chain, starting with the root category down to the current
    # category.  Each chain entry is a dict containing 'id' and `title`.
    cte = Category.get_tree_cte(lambda cat: db.func.json_build_object('id', cat.id, 'title', cat.title))
    query = select([cte.c.path]).where(cte.c.id == Category.id).correlate_except(cte)
    Category.chain = column_property(query, deferred=True)

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

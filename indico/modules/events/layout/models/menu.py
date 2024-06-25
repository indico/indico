# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import g, session
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import joinedload
from werkzeug.utils import cached_property

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.protection import ProtectionMixin
from indico.modules.events.layout.models.principals import MenuEntryPrincipal
from indico.util.enum import RichIntEnum
from indico.util.i18n import _
from indico.util.locators import locator_property
from indico.util.string import format_repr, slugify, text_to_repr
from indico.web.flask.util import url_for


def _get_next_position(context):
    """Get the next menu entry position for the event."""
    event_id = context.current_parameters['event_id']
    parent_id = context.current_parameters['parent_id']
    res = (db.session.query(db.func.max(MenuEntry.position))
           .filter(MenuEntry.event_id == event_id, MenuEntry.parent_id == parent_id)
           .one())
    return (res[0] or 0) + 1


class MenuEntryType(RichIntEnum):
    __titles__ = [None, _('Separator'), _('Internal Link'), _('User Link'), _('Plugin Link'), _('Page')]
    separator = 1
    internal_link = 2
    user_link = 3
    plugin_link = 4
    page = 5


class MenuEntryMixin:
    def __init__(self, **kwargs):
        event = kwargs.pop('event', None)
        super().__init__(**kwargs)
        # XXX: not calling this `event` since this one should NOT use
        # the relationship to avoid mixing data from different DB sessions
        # when updating/populating the menu (which happens in a separate
        # DB session)
        self._event_ref = event
        self.event_id = event.id if event is not None else None

    @property
    def event_ref(self):
        try:
            return self._event_ref
        except AttributeError:
            # needed for MenuEntry objects loaded from the DB
            return self.event

    @property
    def url(self):
        # explicit _external=False since offline site creation forces
        # _external=True if not specified and we want to be able to mangle
        # the generated urls into something suitable as filenames
        if self.is_user_link:
            return self.link_url
        elif (self.is_internal_link or self.is_plugin_link) and not self.default_data.endpoint:
            return None
        elif self.is_internal_link:
            data = self.default_data
            if data.static_site and isinstance(data.static_site, str) and g.get('static_site'):
                return data.static_site
            kwargs = dict(data.url_kwargs)
            if self.name == 'timetable':
                from indico.modules.events.layout import layout_settings
                if layout_settings.get(self.event_ref, 'timetable_by_room'):
                    kwargs['layout'] = 'room'
                if layout_settings.get(self.event_ref, 'timetable_detailed'):
                    start_date = self.event_ref.start_dt_local
                    kwargs['_anchor'] = start_date.strftime('%Y%m%d.detailed')
            return url_for(data.endpoint, self.event_ref, _external=False, **kwargs)
        elif self.is_plugin_link:
            from indico.core.plugins import url_for_plugin
            return url_for_plugin(self.default_data.endpoint, self.event_ref, _external=False)
        elif self.is_page:
            return url_for('event_pages.page_display', self.event_ref, page_id=self.page_id,
                           slug=slugify(self.title, fallback=None), _external=False)
        else:
            return None

    @property
    def is_link(self):
        return self.type in {MenuEntryType.internal_link, MenuEntryType.plugin_link, MenuEntryType.user_link}

    @property
    def is_user_link(self):
        return self.type == MenuEntryType.user_link

    @property
    def is_internal_link(self):
        return self.type == MenuEntryType.internal_link

    @property
    def is_plugin_link(self):
        return self.type == MenuEntryType.plugin_link

    @property
    def is_page(self):
        return self.type == MenuEntryType.page

    @property
    def is_separator(self):
        return self.type == MenuEntryType.separator

    @cached_property
    def default_data(self):
        from indico.modules.events.layout.util import get_menu_entries_from_signal
        if self.name is None:
            return None
        return get_menu_entries_from_signal().get(self.name)

    @property
    def is_orphaned(self):
        return bool(self.name and self.default_data is None)

    @property
    def is_visible(self):
        if not self.is_enabled:
            return False
        if not self.can_access(session.user):
            return False
        if not self.name:
            # we don't have `hide_if_restricted` for custom menu items, so we
            # always hide them if the user cannot access the event
            return self.event_ref.can_access(session.user)
        if self.is_orphaned:
            return False

        data = self.default_data
        if data.hide_if_restricted and not self.event_ref.can_access(session.user):
            return False
        if not data.static_site and g.get('static_site'):
            return False
        return data.visible(self.event_ref)

    @property
    def localized_title(self):
        if self.is_separator:
            return ''

        if self.title is not None:
            return self.title

        defaults = self.default_data
        if defaults is not None:
            return defaults.title

        raise RuntimeError('Tried to get localized title for orphaned menu item')

    @property
    def locator(self):
        return dict(self.event_ref.locator, menu_entry_id=self.id)

    def __repr__(self):
        return f'<{type(self).__name__}({self.id}, {self.title}, {self.name}, position={self.position})>'


class TransientMenuEntry(MenuEntryMixin):
    """
    Transient menu entries are used in case menu customization is disabled. They provide a
    lightweight alternative for the internal links that appear by default.

    :param event: Event -- The event reference the entry applies to
    :param is_enabled: bool -- True, if the entry is enabled
    :param name: str -- The name of the menu entry
    :param position: int -- The position in the menu the entry is at
    :param children: list[MenuEntry] -- The child entries of this menu entry
    :param new_tab: bool -- If the link/page should be opened in a new tab
    """

    def __init__(self, event, is_enabled, name, position, children, new_tab=False):
        super().__init__(event=event)
        self.is_enabled = is_enabled
        self.title = None
        self.name = name
        self.position = position
        self.children = children
        self.new_tab = new_tab
        self.type = None
        self.plugin = None
        self.link_url = None
        self.page_id = None
        self.is_root = True
        for child in self.children:
            child.is_root = False

    @property
    def id(self):
        return self.name

    def can_access(self, user, allow_admin=True):
        return True


class MenuEntry(MenuEntryMixin, ProtectionMixin, db.Model):
    #: Allow speakers in the ProtectionMixin
    allow_speakers = True

    __tablename__ = 'menu_entries'
    __table_args__ = (
        db.CheckConstraint(
            '(type IN ({type.internal_link.value}, {type.plugin_link.value}) AND name IS NOT NULL) OR '  # noqa: UP032
            '(type NOT IN ({type.internal_link.value}, {type.plugin_link.value}) and name IS NULL)'
            .format(type=MenuEntryType),
            'valid_name'),
        db.CheckConstraint(
            f'(type = {MenuEntryType.user_link.value}) = (link_url IS NOT NULL)',
            'valid_link_url'),
        db.CheckConstraint(
            f'(type = {MenuEntryType.page.value} AND page_id IS NOT NULL) OR'
            f' (type != {MenuEntryType.page.value} AND page_id IS NULL)',
            'valid_page_id'),
        db.CheckConstraint(
            f'(type = {MenuEntryType.plugin_link.value} AND plugin IS NOT NULL) OR'
            f' (type != {MenuEntryType.plugin_link.value} AND plugin IS NULL)',
            'valid_plugin'),
        db.CheckConstraint(
            '(type = {type.separator.value} AND title IS NULL) OR'  # noqa: UP032
            ' (type IN ({type.user_link.value}, {type.page.value}) AND title IS NOT NULL) OR'
            ' (type NOT IN ({type.separator.value}, {type.user_link.value}, {type.page.value}))'
            .format(type=MenuEntryType),
            'valid_title'),
        db.CheckConstraint(
            "title != ''",
            'title_not_empty'),
        db.Index(
            None, 'event_id', 'name', unique=True,
            postgresql_where=db.text(
                '(type = {type.internal_link.value} OR type = {type.plugin_link.value})'  # noqa: UP032
                .format(type=MenuEntryType)
            )
        ),
        {'schema': 'events'}
    )

    #: The ID of the menu entry
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the parent menu entry (NULL if root menu entry)
    parent_id = db.Column(
        db.Integer,
        db.ForeignKey('events.menu_entries.id'),
        index=True,
        nullable=True,
    )
    #: The ID of the event which contains the menu
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    #: Whether the entry is visible in the event's menu
    is_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    #: The title of the menu entry (to be displayed to the user)
    title = db.Column(
        db.String,
        nullable=True,
    )
    #: The name of the menu entry (to uniquely identify a default entry for a given event)
    name = db.Column(
        db.String,
        nullable=True
    )
    #: The relative position of the entry in the menu
    position = db.Column(
        db.Integer,
        nullable=False,
        default=_get_next_position
    )
    #: Whether the menu entry should be opened in a new tab or window
    new_tab = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: ACLs for page visibility
    acl_entries = db.relationship(
        'MenuEntryPrincipal',
        backref='menu_entry',
        cascade='all, delete-orphan',
        collection_class=set
    )
    acl = association_proxy('acl_entries', 'principal', creator=lambda v: MenuEntryPrincipal(principal=v))

    #: The target URL of a custom link
    link_url = db.Column(
        db.String,
        nullable=True,
        default=None
    )
    #: The name of the plugin from which the entry comes from (NULL if the entry does not come from a plugin)
    plugin = db.Column(
        db.String,
        nullable=True
    )
    #: The page ID if the entry is a page
    page_id = db.Column(
        db.Integer,
        db.ForeignKey('events.pages.id'),
        nullable=True,
        index=True,
        default=None
    )
    #: The type of the menu entry
    type = db.Column(
        PyIntEnum(MenuEntryType),
        nullable=False
    )

    #: The Event containing the menu entry
    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'menu_entries',
            lazy='dynamic'
        )
    )
    #: The page of the menu entry
    page = db.relationship(
        'EventPage',
        lazy=True,
        cascade='all, delete-orphan',
        single_parent=True,
        backref=db.backref(
            'menu_entry',
            lazy=False,
            uselist=False
        ),
    )
    #: The children menu entries and parent backref
    children = db.relationship(
        'MenuEntry',
        order_by='MenuEntry.position',
        backref=db.backref(
            'parent',
            remote_side=[id]
        ),
    )

    # relationship backrefs:
    # - parent (MenuEntry.children)

    @property
    def is_root(self):
        return self.parent_id is None

    @staticmethod
    def get_for_event(event):
        return (MenuEntry.query.with_parent(event)
                .filter(MenuEntry.parent_id.is_(None))
                .options(joinedload('children'))
                .order_by(MenuEntry.position)
                .all())

    def move(self, to):
        from_ = self.position
        new_pos = to
        value = -1
        if to is None or to < 0:
            new_pos = to = -1

        if from_ > to:
            new_pos += 1
            from_, to = to, from_
            to -= 1
            value = 1

        entries = (MenuEntry.query.with_parent(self.event)
                   .filter(MenuEntry.parent == self.parent,
                           MenuEntry.position.between(from_ + 1, to)))
        for e in entries:
            e.position += value
        self.position = new_pos

    def insert(self, parent, position):
        if position is None or position < 0:
            position = -1
        old_siblings = (MenuEntry.query.with_parent(self.event)
                        .filter(MenuEntry.position > self.position,
                                MenuEntry.parent == self.parent))
        for sibling in old_siblings:
            sibling.position -= 1

        new_siblings = (MenuEntry.query.with_parent(self.event)
                        .filter(MenuEntry.position > position,
                                MenuEntry.parent == parent))
        for sibling in new_siblings:
            sibling.position += 1

        self.parent = parent
        self.position = position + 1

    @property
    def protection_parent(self):
        return self.parent or self.event_ref


class EventPage(db.Model):
    __tablename__ = 'pages'
    __table_args__ = {'schema': 'events'}

    #: The ID of the page
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the event which contains the page
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    #: The rendered HTML of the page
    html = db.Column(
        db.Text,
        nullable=False
    )

    #: The Event which contains the page
    event = db.relationship(
        'Event',
        foreign_keys=[event_id],
        lazy=True,
        backref=db.backref(
            'custom_pages',
            lazy='dynamic'
        )
    )

    # relationship backrefs:
    # - _default_page_of_event (Event.default_page)
    # - legacy_mapping (LegacyPageMapping.page)
    # - menu_entry (MenuEntry.page)

    @locator_property
    def locator(self):
        return dict(self.menu_entry.event.locator, page_id=self.id, slug=slugify(self.menu_entry.title, fallback=None))

    @locator.noslug
    def locator(self):
        return dict(self.menu_entry.event.locator, page_id=self.id)

    @property
    def is_default(self):
        return self.menu_entry.event.default_page_id == self.id

    def __repr__(self):
        return format_repr(self, 'id', _text=text_to_repr(self.html, html=True))

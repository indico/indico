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

from flask import g
from sqlalchemy.orm import joinedload
from werkzeug.utils import cached_property

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.util.i18n import _
from indico.util.string import format_repr, return_ascii, slugify, text_to_repr
from indico.util.struct.enum import RichIntEnum
from indico.web.flask.util import url_for


def _get_next_position(context):
    """Get the next menu entry position for the event."""
    event_id = context.current_parameters['event_id']
    parent_id = context.current_parameters['parent_id']
    res = db.session.query(db.func.max(MenuEntry.position)).filter_by(event_id=event_id, parent_id=parent_id).one()
    return (res[0] or 0) + 1


class MenuEntryType(RichIntEnum):
    __titles__ = [None, _('Separator'), _('Internal Link'), _('User Link'), _('Plugin Link'), _('Page')]
    separator = 1
    internal_link = 2
    user_link = 3
    plugin_link = 4
    page = 5


class MenuEntryMixin(object):
    def __init__(self, **kwargs):
        event = kwargs.pop('event', kwargs.get('event'))
        super(MenuEntryMixin, self).__init__(**kwargs)
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
            if data.static_site and isinstance(data.static_site, basestring) and g.get('static_site'):
                return data.static_site
            kwargs = {}
            if self.name == 'timetable':
                from indico.modules.events. layout import layout_settings
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
            return url_for('event_pages.page_display', self.event_ref, page_id=self.page_id, slug=slugify(self.title),
                           _external=False)
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
        if not self.name:
            return True
        if self.is_orphaned:
            return False

        data = self.default_data
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

    @return_ascii
    def __repr__(self):
        return '<{}({}, {}, {}, position={})>'.format(
            type(self).__name__,
            self.id,
            self.title,
            self.name,
            self.position,
        )


class TransientMenuEntry(MenuEntryMixin):
    def __init__(self, event, is_enabled, name, position, children):
        super(TransientMenuEntry, self).__init__(event=event)
        self.is_enabled = is_enabled
        self.title = None
        self.name = name
        self.position = position
        self.children = children
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


class MenuEntry(MenuEntryMixin, db.Model):
    __tablename__ = 'menu_entries'
    __table_args__ = (
        db.CheckConstraint(
            '(type IN ({type.internal_link.value}, {type.plugin_link.value}) AND name IS NOT NULL) OR '
            '(type NOT IN ({type.internal_link.value}, {type.plugin_link.value}) and name IS NULL)'
            .format(type=MenuEntryType),
            'valid_name'),
        db.CheckConstraint(
            '(type = {type.user_link.value}) = (link_url IS NOT NULL)'
            .format(type=MenuEntryType),
            'valid_link_url'),
        db.CheckConstraint(
            '(type = {type.page.value} AND page_id IS NOT NULL) OR'
            ' (type != {type.page.value} AND page_id IS NULL)'.format(type=MenuEntryType),
            'valid_page_id'),
        db.CheckConstraint(
            '(type = {type.plugin_link.value} AND plugin IS NOT NULL) OR'
            ' (type != {type.plugin_link.value} AND plugin IS NULL)'.format(type=MenuEntryType),
            'valid_plugin'),
        db.CheckConstraint(
            '(type = {type.separator.value} AND title IS NULL) OR'
            ' (type IN ({type.user_link.value}, {type.page.value}) AND title IS NOT NULL) OR'
            ' (type NOT IN ({type.separator.value}, {type.user_link.value}, {type.page.value}))'
            .format(type=MenuEntryType),
            'valid_title'),
        db.CheckConstraint(
            "title != ''",
            'title_not_empty'),
        db.Index(None, 'event_id', 'name', unique=True,
                 postgresql_where=db.text('(type = {type.internal_link.value} OR type = {type.plugin_link.value})'
                                          .format(type=MenuEntryType))),
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

    @property
    def locator(self):
        return dict(self.menu_entry.event.locator, page_id=self.id, slug=slugify(self.menu_entry.title))

    @property
    def is_default(self):
        return self.menu_entry.event.default_page_id == self.id

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', _text=text_to_repr(self.html, html=True))

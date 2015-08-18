# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from werkzeug.utils import cached_property

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.util.i18n import _
from indico.util.string import return_ascii
from indico.util.struct.enum import TitledIntEnum
from indico.web.flask.util import url_for
from MaKaC.conference import ConferenceHolder


def _get_next_position(context):
    """Get the next menu entry position for the event."""
    event_id = context.current_parameters['event_id']
    parent_id = context.current_parameters['parent_id']
    res = db.session.query(db.func.max(MenuEntry.position)).filter_by(event_id=event_id, parent_id=parent_id).one()
    return (res[0] or 0) + 1


class MenuEntryType(TitledIntEnum):
    __titles__ = [None, _('Separator'), _('Internal Link'), _('User Link'), _('Plugin Link'), _('Page')]
    separator = 1
    internal_link = 2
    user_link = 3
    plugin_link = 4
    page = 5


class MenuEntry(db.Model):
    __tablename__ = 'menu_entries'
    __table_args__ = (
        db.CheckConstraint(
            '(type IN ({type.internal_link.value}, {type.plugin_link.value}) AND name IS NOT NULL) OR '
            '(type NOT IN ({type.internal_link.value}, {type.plugin_link.value}) and name IS NULL)'
            .format(type=MenuEntryType),
            'valid_name'),
        db.CheckConstraint(
            '(type IN ({type.separator.value}, {type.page.value}) AND endpoint IS NULL) OR '
            '(type NOT IN ({type.separator.value}, {type.page.value}) AND endpoint IS NOT NULL)'
            .format(type=MenuEntryType),
            'valid_endpoint'),
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
            ' (type != {type.separator.value} AND title IS NOT NULL)'.format(type=MenuEntryType),
            'valid_title'),
        db.UniqueConstraint('event_id', 'position', 'parent_id'),
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
    #: The endpoint of the entry (endpoint for internal and plugin links, url for user links and pages)
    endpoint = db.Column(
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
        db.ForeignKey('events.menu_pages.id'),
        nullable=True,
        default=None
    )
    #: The type of the menu entry
    type = db.Column(
        PyIntEnum(MenuEntryType),
        nullable=False
    )

    #: The Event containing the menu entry
    event_new = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'menu_entries',
            lazy='dynamic'
        )
    )
    #: The page of the menu entry
    page = db.relationship(
        'MenuPage',
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

    @property
    def url(self):
        if self.is_user_link:
            return self.endpoint
        elif self.is_internal_link:
            return url_for(self.endpoint, self.event)
        elif self.is_plugin_link:
            from indico.core.plugins import url_for_plugin
            return url_for_plugin(self.endpoint, self.event)
        elif self.is_page:
            return url_for('event_pages.page_display', self.event, page_id=self.page_id)
        return None

    @property
    def is_root(self):
        return self.parent_id is None

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

        return self.default_data.visible(self.event)

    @property
    def is_default_title(self):
        defaults = self.default_data
        return defaults.title == self.title if defaults is not None else False

    @cached_property
    def event(self):
        return ConferenceHolder().getById(str(self.event_id), True)

    @property
    def locator(self):
        return dict(self.event.getLocator(), menu_entry_id=self.id)

    @classmethod
    def get_for_event(cls, event):
        return cls.find(event_id=int(event.id), parent_id=None, _eager=cls.children).order_by(MenuEntry.position).all()

    @return_ascii
    def __repr__(self):
        return '<MenuEntry({}, {}, {}{})>'.format(
            self.id,
            self.title,
            self.endpoint,
            ', is_root=True' if self.is_root else '',
        )


class MenuPage(db.Model):
    __tablename__ = 'menu_pages'
    __table_args__ = {'schema': 'events'}

    #: The ID of the page
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The rendered HTML of the page
    html = db.Column(
        db.Text,
        nullable=False
    )

    @property
    def locator(self):
        return dict(self.menu_entry.event.getLocator(), page_id=self.id)

    @return_ascii
    def __repr__(self):
        return '<MenuPage({}, {})>'.format(self.id, self.html)

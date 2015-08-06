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
from indico.core.plugins import url_for_plugin
from indico.util.i18n import _
from indico.util.string import return_ascii
from indico.util.struct.enum import TitledIntEnum
from indico.web.flask.util import url_for
from MaKaC.conference import ConferenceHolder


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
            '(type = {type.separator.value} AND link IS NULL AND page_id is NULL) OR'
            ' (type in ({type.internal_link.value}, {type.user_link.value}, {type.plugin_link.value})'
            ' AND link IS NOT NULL AND page_id is NULL) OR'
            ' (type = {type.page.value} AND link IS NULL AND page_id is NOT NULL)'.format(type=MenuEntryType),
            'valid_type'),
        db.CheckConstraint(
            '((type = {type.internal_link.value} OR type = {type.plugin_link.value}) AND endpoint IS NOT NULL) OR'
            ' (type in ({type.separator.value}, {type.user_link.value}, {type.page.value}) AND endpoint is NULL)'
            .format(type=MenuEntryType),
            'valid_endpoint'),
        db.CheckConstraint(
            '(type = {type.plugin_link.value} AND plugin IS NOT NULL) OR plugin is NULL'.format(type=MenuEntryType),
            'valid_plugin'),
        {'schema': 'events'}
    )

    #: The ID of the attachment
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
        index=True,
        nullable=False
    )
    #: Whether the entry is visible in the event's menu
    visible = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    #: The name of the menu entry
    title = db.Column(
        db.String,
        nullable=False,
    )
    #: The position of the entry relative to the start in the menu
    position = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )
    #: Whether the menu entry should be opened in a new tab or window
    new_tab = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: The endpoint of the link for internal and plugin links
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
    #: The page data if the entry is a page
    page_id = db.Column(
        db.Integer,
        db.ForeignKey('events.menu_pages.id'),
        nullable=True,
        default=None
    )
    #: The type of the attachment (file or link)
    type = db.Column(
        PyIntEnum(MenuEntryType),
        nullable=False
    )
    #: The page of the menu entry
    page = db.relationship(
        'MenuPage',
        primaryjoin=lambda: MenuEntry.page_id == MenuPage.id,
        foreign_keys=page_id,
        lazy=False,
        post_update=True
    )

    #: The parent menu entry
    children = db.relationship(
        'MenuEntry',
        cascade="all, delete-orphan",
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
            return url_for_plugin(self.endpoint, self.event)
        elif self.is_page:
            #TODO: handle page url
            pass
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
    def is_page(self):
        return self.type == MenuEntryType.page

    @property
    def is_separator(self):
        return self.type == MenuEntryType.separator

    @cached_property
    def event(self):
        return ConferenceHolder().getById(str(self.event_id), True)

    @property
    def locator(self):
        return dict(self.event.getLocator(), menu_entry_id=self.id)

    @return_ascii
    def __repr__(self):
        return '<MenuEntry({}, {}, {}{}{})>'.format(
            self.id,
            self.title,
            'page' if self.is_page else (self.link if self.is_link else 'separator'),
            ', internal=False' if self.is_user_link else (', internal=True' if self.is_link else ''),
            ', is_root=True' if self.is_root else '',
        )


class MenuPage(db.Model):
    __tablename__ = 'menu_pages'
    __table_args__ = {'schema': 'events'}

    #: The ID of the file
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the associated menu entry
    menu_entry_id = db.Column(
        db.Integer,
        db.ForeignKey('events.menu_entries.id'),
        nullable=False,
        index=True
    )
    #: The rendered HTML of the note
    html = db.Column(
        db.Text,
        nullable=False
    )

    @return_ascii
    def __repr__(self):
        return '<MenuPage({}, {})>'.format(self.id, self.html)

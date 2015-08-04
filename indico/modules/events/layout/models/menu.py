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

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.util.i18n import _
from indico.util.string import return_ascii
from indico.util.struct.enum import TitledIntEnum


class MenuEntryType(TitledIntEnum):
    __titles__ = [None, _('Separator'), _('Internal Link'), _('External Link'), _('Plugin Link'), _('Page')]
    separator = 1
    internal_link = 2
    external_link = 3
    plugin_link = 4
    page = 5


class MenuEntry(db.Model):
    __tablename__ = 'menu_entries'
    __table_args__ = (
        db.CheckConstraint(
            '(type = {type.separator.value} AND link IS NULL AND page_id is NULL) OR'
            ' (type in ({type.internal_link.value}, {type.external_link.value}, {type.plugin_link.value})'
            ' AND link IS NOT NULL AND page_id is NULL) OR'
            ' (type = {type.page.value} AND link IS NULL AND page_id is NOT NULL)'.format(type=MenuEntryType),
            'valid_type'),
        db.CheckConstraint(
            '((type = {type.internal_link.value} OR type = {type.plugin_link.value}) AND endpoint IS NOT NULL) OR'
            ' (type in ({type.separator.value}, {type.external_link.value}, {type.page.value}) AND endpoint is NULL)'
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
    #: The link data if the entry is a link
    link = db.Column(
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
    # #: The parent menu entry
    # parent = db.relationship(
    #     'MenuEntry',
    #     remote_side=[id]
    #     # primaryjoin=lambda: MenuEntry.parent_id == MenuEntry.id,
    #     # foreign_keys=parent_id,
    #     # lazy=False,
    #     # post_update=True
    # )

    #: The parent menu entry
    children = db.relationship(
        'MenuEntry',
        cascade="all, delete-orphan",
        # primaryjoin=lambda: MenuEntry.id == MenuEntry.parent_id,
        # foreign_keys=lambda: MenuEntry.id,
        order_by='MenuEntry.position',
        backref=db.backref(
            'parent',
            remote_side=[id]
        ),
    )

    @property
    def is_root(self):
        return self.parent_id is None

    @return_ascii
    def __repr__(self):
        return '<MenuEntry({}, {}, {}{}, {}, {})>'.format(
            self.id,
            self.title,
            ('page' if self.type == MenuEntryType.page else
                self.link_url if self.type == MenuEntryType.link
                else 'separator'),
            ', is_root=True' if self.is_root else '',
            self.protection_repr,
            self.folder_id
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

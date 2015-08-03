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
    __titles__ = [None, _('Separator'), _('Link'), _('Page')]
    separator = 1
    link = 2
    page = 3


class MenuEntry(db.Model):
    __tablename__ = 'menu_entries'
    __table_args__ = (
        db.CheckConstraint(
            '(type == {type.separator.value} AND link IS NULL AND page is NULL) OR'
            '(type == {type.link.value} AND link IS NOT NULL AND page is NULL) OR'
            '(type == {type.page.value} AND link IS NULL AND page is NOT NULL)'.format(type=MenuEntryType),
            'valid_type'),
        {'schema': 'menu_entries'}
    )

    #: The ID of the attachment
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the parent menu entry (NULL if root menu entry)
    parent_id = db.Column(
        db.Integer,
        db.ForeignKey('menu_entries.id'),
        index=True,
        nullable=True,
    )
    #: The ID of the event which contains the menu
    event_id = db.Column(
        db.Integer,
        index=True,
        nullable=False
    )
    #: Whether the entry is enabled and visible in the event's menu
    enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: The name of the menu entry
    title = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    #: The position of the entry relative to the start in the menu
    position = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )
    #: The link data if the entry is a link
    link_id = db.Column(
        db.Integer,
        db.ForeignKey('menu_links.id'),
        nullable=False
    )
    #: The page data if the entry is a page
    page_id = db.Column(
        db.Integer,
        db.ForeignKey('menu_pages.id'),
        nullable=False
    )
    #: The type of the attachment (file or link)
    type = db.Column(
        PyIntEnum(MenuEntryType),
        nullable=False
    )
    #: The link of the menu entry
    link = db.relationship(
        'MenuEntryLink',
        primaryjoin=lambda: MenuEntry.link_id == MenuEntryLink.id,
        foreign_keys=link_id,
        lazy=False,
        post_update=True
    )
    #: The page of the menu entry
    page = db.relationship(
        'MenuEntryPage',
        primaryjoin=lambda: MenuEntry.page_id == MenuEntryPage.id,
        foreign_keys=page_id,
        lazy=False,
        post_update=True
    )
    #: The parent menu entry
    parent = db.relationship(
        'MenuEntry',
        primaryjoin=lambda: MenuEntry.parent_id == MenuEntry.id,
        foreign_keys=parent_id,
        lazy=False,
        post_update=True
    )

    #: The parent menu entry
    children = db.relationship(
        'MenuEntry',
        primaryjoin=lambda: MenuEntry.id == MenuEntry.parent_id,
        foreign_keys=lambda: MenuEntry.id,
        order_by='MenuEntry.position',
        backref=db.backref(
            'menu_entries',
            remote_side=parent_id
        )
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


class MenuEntryLink(db.Model):
    __tablename__ = 'entry_links'
    __table_args__ = {'schema': 'entry_links'}

    #: The ID of the link entry
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the associated attachment
    menu_entry_id = db.Column(
        db.Integer,
        db.ForeignKey('attachments.attachments.id'),
        nullable=False,
        index=True
    )
    #: The target URL for a link menu entry
    url = db.Column(
        db.String,
        nullable=False
    )
    #: Whether the link points to a page within Indico
    is_internal = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Whether the link is injected from a plugin
    from_plugin = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Whether the link should be opened in a new tab or window
    in_new_tab = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    @return_ascii
    def __repr__(self):
        return '<MenuEntryLink({}, {})>'.format(self.id, self.url)


class MenuEntryPage(db.Model):
    __tablename__ = 'entry_pages'
    __table_args__ = {'schema': 'entry_pages'}

    #: The ID of the file
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the associated attachment
    menu_entry_id = db.Column(
        db.Integer,
        db.ForeignKey('attachments.attachments.id'),
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
        return '<MenuEntryPage({}, {})>'.format(self.id, self.html)

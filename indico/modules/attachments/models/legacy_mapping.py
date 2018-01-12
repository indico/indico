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

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.util.string import return_ascii


class _LegacyLinkMixin(object):
    events_backref_name = None

    @declared_attr
    def event_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey('events.events.id'),
            nullable=False,
            index=True
        )

    @declared_attr
    def session_id(cls):
        return db.Column(
            db.String,
            nullable=True
        )

    @declared_attr
    def contribution_id(cls):
        return db.Column(
            db.String,
            nullable=True
        )

    @declared_attr
    def subcontribution_id(cls):
        return db.Column(
            db.String,
            nullable=True
        )

    @declared_attr
    def event(cls):
        return db.relationship(
            'Event',
            lazy=True,
            backref=db.backref(
                cls.events_backref_name,
                lazy='dynamic'
            )
        )

    @property
    def link_repr(self):
        """A kwargs-style string suitable for the object's repr"""
        _all_columns = {'event_id', 'contribution_id', 'subcontribution_id', 'session_id'}
        info = [(key, getattr(self, key)) for key in _all_columns if getattr(self, key) is not None]
        return ', '.join('{}={}'.format(key, value) for key, value in info)


class LegacyAttachmentFolderMapping(_LegacyLinkMixin, db.Model):
    """Legacy attachmentfolder id mapping

    Legacy folders ("materials") had ids unique only within their
    linked object.  This table maps those ids for a specific object
    to the new globally unique folder id.
    """

    __tablename__ = 'legacy_folder_id_map'
    events_backref_name = 'all_legacy_attachment_folder_mappings'

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls, schema='attachments')

    material_id = db.Column(
        db.String,
        nullable=False
    )
    folder_id = db.Column(
        db.Integer,
        db.ForeignKey('attachments.folders.id'),
        primary_key=True,
        autoincrement=False
    )
    folder = db.relationship(
        'AttachmentFolder',
        lazy=False,
        backref=db.backref('legacy_mapping', uselist=False, lazy=True)
    )

    @return_ascii
    def __repr__(self):
        return '<LegacyAttachmentFolderMapping({}, material_id={}, {})>'.format(
            self.folder, self.material_id, self.link_repr
        )


class LegacyAttachmentMapping(_LegacyLinkMixin, db.Model):
    """Legacy attachment id mapping

    Legacy attachments ("resources") had ids unique only within their
    folder and its linked object.  This table maps those ids for a
    specific object to the new globally unique attachment id.
    """

    __tablename__ = 'legacy_attachment_id_map'
    events_backref_name = 'all_legacy_attachment_mappings'

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls, schema='attachments')

    material_id = db.Column(
        db.String,
        nullable=False
    )
    resource_id = db.Column(
        db.String,
        nullable=False
    )
    attachment_id = db.Column(
        db.Integer,
        db.ForeignKey('attachments.attachments.id'),
        primary_key=True,
        autoincrement=False
    )
    attachment = db.relationship(
        'Attachment',
        lazy=False,
        backref=db.backref('legacy_mapping', uselist=False, lazy=True)
    )

    @return_ascii
    def __repr__(self):
        return '<LegacyAttachmentMapping({}, material_id={}, resource_id={}, {})>'.format(
            self.attachment, self.material_id, self.resource_id, self.link_repr
        )

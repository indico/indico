# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

import posixpath

from indico.core.config import Config
from indico.core.db import db
from indico.core.storage.models import StoredFileMixin
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii, strict_unicode


class PaperTemplate(StoredFileMixin, db.Model):
    __tablename__ = 'templates'
    __table_args__ = {'schema': 'event_paper_reviewing'}

    # StoredFileMixin settings
    add_file_date_column = False

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    name = db.Column(
        db.String,
        nullable=False
    )
    description = db.Column(
        db.Text,
        nullable=False,
        default=''
    )

    event_new = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'paper_templates',
            cascade='all, delete-orphan',
            lazy=True
        )
    )

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'event_id', 'filename', content_type=None)

    @locator_property
    def locator(self):
        return dict(self.event_new.locator, template_id=self.id, filename=self.filename)

    def _build_storage_path(self):
        self.assign_id()
        path_segments = ['event', strict_unicode(self.event_new.id), 'paper_templates']
        path = posixpath.join(*(path_segments + ['{}_{}'.format(self.id, self.filename)]))
        return Config.getInstance().getAttachmentStorage(), path

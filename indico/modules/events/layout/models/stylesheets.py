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

import posixpath


from indico.core.config import Config
from indico.core.db import db
from indico.core.storage import StoredFileMixin
from indico.util.string import return_ascii


class StylesheetFile(StoredFileMixin, db.Model):
    __tablename__ = 'css_files'
    __table_args__ = {'schema': 'events'}

    # CSS files are not version-controlled
    version_of = None

    #: The ID of the file
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    #: The event the CSS file belongs to
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        unique=True,
        nullable=False,
        index=True
    )

    event_new = db.relationship(
        'Event',
        lazy=False,
        backref=db.backref(
            'layout_stylesheets',
            lazy='dynamic'
        )
    )

    @property
    def locator(self):
        return dict(self.event_new.locator, css_id=self.id)

    def _build_storage_path(self):
        path_segments = ['event', unicode(self.event_id), 'stylesheets']
        self.assign_id()
        filename = '{}-{}'.format(self.id, self.filename)
        path = posixpath.join(*(path_segments + [filename]))
        return Config.getInstance().getAttachmentStorage(), path

    @return_ascii
    def __repr__(self):
        return '<StylesheetFile({}, {}, {})>'.format(
            self.id,
            self.event_id,
            self.filename
        )

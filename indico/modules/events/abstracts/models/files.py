# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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
from indico.util.string import format_repr, return_ascii, text_to_repr, strict_unicode


class AbstractFile(StoredFileMixin, db.Model):
    __tablename__ = 'files'
    __table_args__ = {'schema': 'event_abstracts'}

    # StoredFileMixin settings
    add_file_date_column = False

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    abstract_id = db.Column(
        db.Integer,
        db.ForeignKey('event_abstracts.abstracts.id'),
        nullable=False,
        index=True
    )
    abstract = db.relationship(
        'Abstract',
        lazy=True,
        backref=db.backref(
            'files',
            lazy=True
        )
    )

    @property
    def locator(self):
        return dict(self.abstract.locator, file_id=self.id, filename=self.filename)

    def _build_storage_path(self):
        self.abstract.assign_id()
        path_segments = ['event', strict_unicode(self.abstract.event_new.id),
                         'abstracts', strict_unicode(self.abstract.id)]
        self.assign_id()
        filename = '{}-{}'.format(self.id, self.filename)
        path = posixpath.join(*(path_segments + [filename]))
        return Config.getInstance().getAttachmentStorage(), path

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'abstract_id', content_type=None, _text=text_to_repr(self.filename))

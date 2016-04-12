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
from indico.core.storage.models import StoredFileMixin
from indico.util.string import format_repr, return_ascii, strict_unicode


class PaperFile(StoredFileMixin, db.Model):
    """Represents a file belonging to a paper that is under review (contribution)."""

    __tablename__ = 'paper_files'
    __table_args__ = {'schema': 'event_paper_reviewing'}

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    contribution_id = db.Column(
        db.Integer,
        db.ForeignKey('events.contributions.id'),
        index=True,
        nullable=False
    )
    revision_id = db.Column(
        db.Integer
    )
    contribution = db.relationship(
        'Contribution',
        lazy=False,
        backref=db.backref(
            'paper_files',
            lazy='dynamic'
        )
    )

    @property
    def locator(self):
        return dict(self.contribution.locator, paper_file_id=self.id, filename=self.filename)

    def _build_storage_path(self):
        self.assign_id()
        path_segments = ['event', strict_unicode(self.contribution.event_new.id), 'papers',
                         "{}_{}".format(self.id, strict_unicode(self.contribution.id))]
        path = posixpath.join(*(path_segments + [self.filename]))
        return Config.getInstance().getAttachmentStorage(), path

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'contribution_id', 'filename', 'content_type')

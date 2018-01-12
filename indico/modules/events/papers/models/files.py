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

import posixpath

from indico.core.config import config
from indico.core.db import db
from indico.core.storage.models import StoredFileMixin
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii, strict_unicode, text_to_repr


class PaperFile(StoredFileMixin, db.Model):
    __tablename__ = 'files'
    __table_args__ = {'schema': 'event_paper_reviewing'}

    # StoredFileMixin settings
    add_file_date_column = False

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    _contribution_id = db.Column(
        'contribution_id',
        db.Integer,
        db.ForeignKey('events.contributions.id'),
        index=True,
        nullable=False
    )
    revision_id = db.Column(
        db.Integer,
        db.ForeignKey('event_paper_reviewing.revisions.id'),
        index=True,
        nullable=True
    )

    _contribution = db.relationship(
        'Contribution',
        lazy=True,
        backref=db.backref(
            '_paper_files',
            lazy=True
        )
    )
    paper_revision = db.relationship(
        'PaperRevision',
        lazy=True,
        backref=db.backref(
            'files',
            lazy=True,
            cascade='all, delete-orphan'
        )
    )

    def __init__(self, *args, **kwargs):
        paper = kwargs.pop('paper', None)
        if paper:
            kwargs.setdefault('_contribution', paper.contribution)
        super(PaperFile, self).__init__(*args, **kwargs)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', '_contribution_id', content_type=None, _text=text_to_repr(self.filename))

    @locator_property
    def locator(self):
        return dict(self.paper.locator, file_id=self.id, filename=self.filename)

    @property
    def paper(self):
        return self._contribution.paper

    @paper.setter
    def paper(self, paper):
        self._contribution = paper.contribution

    def _build_storage_path(self):
        self.assign_id()
        path_segments = ['event', strict_unicode(self._contribution.event.id), 'papers',
                         '{}_{}'.format(self.id, strict_unicode(self._contribution.id))]
        path = posixpath.join(*(path_segments + [self.filename]))
        return config.ATTACHMENT_STORAGE, path

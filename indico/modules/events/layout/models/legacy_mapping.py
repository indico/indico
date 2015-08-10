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
from indico.util.string import return_ascii


class LegacyImageMapping(db.Model):
    """Legacy image id mapping

    Legacy images had event-unique numeric ids. Using this
    mapping we can resolve old ones to their new id.
    """

    __tablename__ = 'legacy_image_id_map'
    __table_args__ = {'schema': 'events'}

    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        primary_key=True,
        index=True
    )
    legacy_image_id = db.Column(
        db.Integer,
        primary_key=True,
        index=True
    )
    image_id = db.Column(
        db.Integer,
        db.ForeignKey('events.image_files.id'),
        nullable=False
    )

    @return_ascii
    def __repr__(self):
        return '<LegacyImageMapping({}, {})>'.format(self.legacy_image_id, self.image_id)

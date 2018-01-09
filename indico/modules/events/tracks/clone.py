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

from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.cloning import EventCloner
from indico.modules.events.models.events import EventType
from indico.modules.events.tracks.models.tracks import Track
from indico.util.i18n import _


class TrackCloner(EventCloner):
    name = 'tracks'
    friendly_name = _('Tracks')
    always_available_dep = True

    @property
    def is_visible(self):
        return self.old_event.type_ == EventType.conference

    @property
    def is_available(self):
        return bool(self.old_event.tracks)

    @no_autoflush
    def run(self, new_event, cloners, shared_data):
        self._track_map = {}
        self._clone_tracks(new_event)
        db.session.flush()
        return {'track_map': self._track_map}

    def _clone_tracks(self, new_event):
        attrs = get_simple_column_attrs(Track) | {'abstract_reviewers', 'conveners'}
        for old_track in self.old_event.tracks:
            track = Track()
            track.populate_from_attrs(old_track, attrs)
            new_event.tracks.append(track)
            self._track_map[old_track] = track

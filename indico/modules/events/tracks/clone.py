# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import clone_principals
from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.cloning import EventCloner
from indico.modules.events.models.events import EventType
from indico.modules.events.tracks.models.groups import TrackGroup
from indico.modules.events.tracks.models.principals import TrackPrincipal
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
        return self._has_content(self.old_event)

    def has_conflicts(self, target_event):
        return self._has_content(target_event)

    @no_autoflush
    def run(self, new_event, cloners, shared_data, event_exists=False):
        self._track_map = {}
        self._track_group_map = {}
        self._clone_track_groups(new_event)
        self._clone_tracks(new_event)
        db.session.flush()
        return {'track_map': self._track_map}

    def _has_content(self, event):
        return bool(event.tracks)

    def _clone_tracks(self, new_event):
        attrs = get_simple_column_attrs(Track)
        for old_track in self.old_event.tracks:
            track = Track()
            track.populate_from_attrs(old_track, attrs)
            track.acl_entries = clone_principals(TrackPrincipal, old_track.acl_entries)
            track.track_group = self._track_group_map.get(old_track.track_group, None)
            new_event.tracks.append(track)
            self._track_map[old_track] = track

    def _clone_track_groups(self, new_event):
        attrs = get_simple_column_attrs(TrackGroup)
        for old_group in self.old_event.track_groups:
            group = TrackGroup()
            group.populate_from_attrs(old_group, attrs)
            new_event.track_groups.append(group)
            self._track_group_map[old_group] = group

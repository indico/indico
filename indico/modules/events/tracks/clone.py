# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import clone_principals
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.cloning import EventCloner, get_attrs_to_clone
from indico.modules.events.models.events import EventType
from indico.modules.events.tracks.models.groups import TrackGroup
from indico.modules.events.tracks.models.principals import TrackPrincipal
from indico.modules.events.tracks.models.tracks import Track
from indico.modules.events.tracks.settings import track_settings
from indico.util.i18n import _


class TrackCloner(EventCloner):
    name = 'tracks'
    friendly_name = _('Tracks and scientific program')
    always_available_dep = True

    @property
    def is_visible(self):
        return self.old_event.type_ == EventType.conference

    @property
    def is_available(self):
        return self._has_content(self.old_event)

    def get_conflicts(self, target_event):
        if self._has_content(target_event):
            return [_('The target event already has tracks or a program')]

    @no_autoflush
    def run(self, new_event, cloners, shared_data, event_exists=False):
        self._track_map = {}
        self._track_group_map = {}
        self._clone_program(new_event)
        self._clone_track_groups(new_event)
        self._clone_tracks(new_event)
        db.session.flush()
        return {'track_map': self._track_map}

    def _has_content(self, event):
        return bool(event.tracks) or bool(track_settings.get(event, 'program'))

    def _clone_program(self, new_event):
        track_settings.set_multi(new_event, track_settings.get_all(self.old_event, no_defaults=True))

    def _clone_tracks(self, new_event):
        attrs = get_attrs_to_clone(Track)
        for old_track in self.old_event.tracks:
            track = Track()
            track.populate_from_attrs(old_track, attrs)
            track.acl_entries = clone_principals(TrackPrincipal, old_track.acl_entries)
            track.track_group = self._track_group_map.get(old_track.track_group, None)
            new_event.tracks.append(track)
            self._track_map[old_track] = track

    def _clone_track_groups(self, new_event):
        attrs = get_attrs_to_clone(TrackGroup)
        for old_group in self.old_event.track_groups:
            group = TrackGroup()
            group.populate_from_attrs(old_group, attrs)
            new_event.track_groups.append(group)
            self._track_group_map[old_group] = group

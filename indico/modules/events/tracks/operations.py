# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session

from indico.core.db import db
from indico.modules.events.tracks import logger
from indico.modules.events.tracks.models.groups import TrackGroup
from indico.modules.events.tracks.models.tracks import Track
from indico.modules.events.tracks.settings import track_settings
from indico.modules.logs import EventLogRealm, LogKind


def create_track(event, data):
    track = Track(event=event)
    track.populate_from_dict(data)
    db.session.flush()
    logger.info('Track %r created by %r', track, session.user)
    event.log(EventLogRealm.management, LogKind.positive, 'Tracks',
              f'Track "{track.title}" has been created.', session.user)
    return track


def update_track(track, data):
    track.populate_from_dict(data)
    db.session.flush()
    logger.info('Track %r modified by %r', track, session.user)
    track.event.log(EventLogRealm.management, LogKind.change, 'Tracks',
                    f'Track "{track.title}" has been modified.', session.user)


def delete_track(track):
    db.session.delete(track)
    logger.info('Track deleted by %r: %r', session.user, track)


def update_program(event, data):
    track_settings.set_multi(event, data)
    logger.info('Program of %r updated by %r', event, session.user)
    event.log(EventLogRealm.management, LogKind.change, 'Tracks', 'The program has been updated', session.user)


def create_track_group(event, data):
    track_group = TrackGroup()
    track_group.event = event
    track_group.populate_from_dict(data)
    db.session.flush()
    logger.info('Track group %r created by %r', track_group, session.user)
    event.log(EventLogRealm.management, LogKind.positive, 'Track Groups',
              f'Track group "{track_group.title}" has been created.', session.user)


def update_track_group(track_group, data):
    track_group.populate_from_dict(data)
    db.session.flush()
    logger.info('Track group %r updated by %r', track_group, session.user)
    track_group.event.log(EventLogRealm.management, LogKind.positive, 'Track Groups',
                          f'Track group "{track_group.title}" has been updated.', session.user)


def delete_track_group(track_group):
    db.session.delete(track_group)
    logger.info('Track group deleted by %r: %r', session.user, track_group)

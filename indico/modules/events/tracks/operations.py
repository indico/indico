# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import session

from indico.core.db import db
from indico.modules.events.logs import EventLogKind, EventLogRealm
from indico.modules.events.tracks import logger
from indico.modules.events.tracks.models.tracks import Track
from indico.modules.events.tracks.settings import track_settings


def create_track(event, data):
    track = Track(event=event)
    track.populate_from_dict(data)
    db.session.flush()
    logger.info('Track %r created by %r', track, session.user)
    event.log(EventLogRealm.management, EventLogKind.positive, 'Tracks',
              'Track "{}" has been created.'.format(track.title), session.user)
    return track


def update_track(track, data):
    track.populate_from_dict(data)
    db.session.flush()
    logger.info('Track %r modified by %r', track, session.user)
    track.event.log(EventLogRealm.management, EventLogKind.change, 'Tracks',
                    'Track "{}" has been modified.'.format(track.title), session.user)


def delete_track(track):
    db.session.delete(track)
    logger.info('Track deleted by %r: %r', session.user, track)


def update_program(event, data):
    track_settings.set_multi(event, data)
    logger.info('Program of %r updated by %r', event, session.user)
    event.log(EventLogRealm.management, EventLogKind.change, 'Tracks', 'The program has been updated', session.user)

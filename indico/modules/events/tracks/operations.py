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

from flask import session

from indico.core.db import db
from indico.modules.events.logs import EventLogKind, EventLogRealm
from indico.modules.events.tracks import logger
from indico.modules.events.tracks.models.tracks import Track


def create_track(event, data):
    track = Track(event_new=event)
    track.populate_from_dict(data)
    db.session.flush()
    logger.info('Track %r created by %s', track, session.user)
    event.log(EventLogRealm.management, EventLogKind.positive, 'Tracks',
              'Track "{}" has been created.'.format(track.title), session.user)
    return track

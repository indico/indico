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

from indico.core import signals
from indico.core.db import db
from indico.core.logger import Logger
from indico.modules.events.static.models.static import StaticSite

logger = Logger.get('events.static')


@signals.event.deleted.connect
def _event_deleted(event, **kwargs):
    if not event.id.isdigit():
        return
    for static_site in StaticSite.find(event_id=int(event.id)):
        db.session.delete(static_site)

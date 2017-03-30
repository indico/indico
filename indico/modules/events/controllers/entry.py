# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from flask import redirect, request, url_for, current_app
from werkzeug.exceptions import NotFound

from indico.core.db import db
from indico.modules.events import Event
from indico.modules.events.controllers.display import RHDisplayEvent
from indico.modules.events.models.legacy_mapping import LegacyEventMapping
from indico.util.i18n import _
from indico.util.string import is_legacy_id


def event_or_shorturl(confId, shorturl_namespace=False, force_overview=False):
    func = None
    event_ = Event.get(int(confId)) if confId.isdigit() else None
    if event_ and event_.is_deleted:
        raise NotFound(_('This event has been deleted.'))
    elif event_:
        # For obvious reasons an event id always comes first.
        # If it's used within the short url namespace we redirect to the event namespace, otherwise
        # we call the RH to display the event
        if shorturl_namespace:
            func = lambda: redirect(event_.url)
        else:
            params = request.args.to_dict()
            params['confId'] = confId
            request.view_args['confId'] = int(request.view_args['confId'])
            func = lambda: RHDisplayEvent().process(params)
    else:
        shorturl_event = (Event.query
                          .filter(db.func.lower(Event.url_shortcut) == confId.lower(),
                                  ~Event.is_deleted)
                          .one_or_none())
        if (shorturl_namespace or current_app.config['INDICO_COMPAT_ROUTES']) and shorturl_event:
            if shorturl_namespace:
                # Correct namespace => redirect to the event
                func = lambda: redirect(shorturl_event.url)
            else:
                # Old event namespace => 301-redirect to the new shorturl first to get Google etc. to update it
                func = lambda: redirect(shorturl_event.short_url, 301)
        elif is_legacy_id(confId):
            mapping = LegacyEventMapping.find_first(legacy_event_id=confId)
            if mapping is not None:
                url = url_for('events.display', confId=mapping.event_id)
                func = lambda: redirect(url, 301)

    if func is None:
        raise NotFound(_('An event with this ID/shortcut does not exist.'))
    return func()

# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import redirect, request, url_for
from werkzeug.exceptions import NotFound

from indico.core.config import config
from indico.core.db import db
from indico.modules.events import Event
from indico.modules.events.controllers.display import RHDisplayEvent
from indico.modules.events.models.legacy_mapping import LegacyEventMapping
from indico.util.i18n import _
from indico.util.string import is_legacy_id


# XXX: force_overview is not used by passed by flask, so it needs to remain here
def event_or_shorturl(event_id, shorturl_namespace=False, force_overview=False):
    event = Event.get(int(event_id)) if event_id.isdigit() and (event_id[0] != '0' or event_id == '0') else None
    if event and event.is_deleted:
        raise NotFound(_('This event has been deleted.'))
    elif event:
        # For obvious reasons an event id always comes first.
        # If it's used within the short url namespace we redirect to the event namespace, otherwise
        # we call the RH to display the event
        if shorturl_namespace:
            return redirect(event.url)
        elif not request.path.endswith('/'):
            return redirect(event.url, 301)
        else:
            request.view_args['event_id'] = int(event_id)
            return RHDisplayEvent().process()
    else:
        shorturl_event = (Event.query
                          .filter(db.func.lower(Event.url_shortcut) == event_id.lower(),
                                  ~Event.is_deleted)
                          .one_or_none())
        if (shorturl_namespace or config.ROUTE_OLD_URLS) and shorturl_event:
            if shorturl_namespace:
                # Correct namespace => redirect to the event
                return redirect(shorturl_event.url)
            else:
                # Old event namespace => 301-redirect to the new shorturl first to get Google etc. to update it
                return redirect(shorturl_event.short_url, 301)
        elif is_legacy_id(event_id):
            mapping = LegacyEventMapping.query.filter_by(legacy_event_id=event_id).first()
            if mapping is not None:
                url = url_for('events.display', event_id=mapping.event_id)
                return redirect(url, 301)

    raise NotFound(_('An event with this ID/shortcut does not exist.'))

# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import redirect, request, url_for
from werkzeug.exceptions import NotFound

from indico.core.config import config
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
            request.view_args['confId'] = int(request.view_args['confId'])
            func = lambda: RHDisplayEvent().process()
    else:
        shorturl_event = (Event.query
                          .filter(db.func.lower(Event.url_shortcut) == confId.lower(),
                                  ~Event.is_deleted)
                          .one_or_none())
        if (shorturl_namespace or config.ROUTE_OLD_URLS) and shorturl_event:
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

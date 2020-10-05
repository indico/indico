# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from uuid import uuid4

from flask import jsonify, request
from webargs import fields

from indico.legacy.common.cache import GenericCache
from indico.web.args import use_kwargs
from indico.web.rh import RH


class RHPrepareEvent(RH):
    """Prepare a new event, store it using GenericCache util, and create a UUID."""

    CSRF_ENABLED = False
    _cache = GenericCache('event-preparation')

    @use_kwargs({
        'title': fields.String(missing=""),
        'start_dt': fields.String(missing=""),
        'duration': fields.Integer(),
    })
    def _process(self, title, start_dt, duration):
        event_key = unicode(uuid4())
        self._cache.set(
            event_key,
            {
                "title": title,
                "start_dt": start_dt,
                "duration": duration,
                },
            90
        )
        return jsonify(url="{}#create-event:meeting::{}".format(request.url_root, event_key))

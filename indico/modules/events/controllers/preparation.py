# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.


from uuid import uuid4

from flask import jsonify
from pytz import timezone
from webargs import fields

from indico.legacy.common.cache import GenericCache
from indico.util.marshmallow import NaiveDateTime
from indico.web.args import use_kwargs
from indico.web.rh import RH
from indico.web.util import url_for_index


class RHPrepareEvent(RH):
    """Prepare a new event, store it using GenericCache util, and create a UUID."""

    CSRF_ENABLED = False

    @use_kwargs({
        'title': fields.String(required=True),
        'start_dt': NaiveDateTime(required=True),
        'tz': fields.String(),
        'duration': fields.Integer(),
    })
    def _process(self, title, start_dt, tz, duration):
        event_key = str(uuid4())
        cache = GenericCache('event-preparation')
        start_dt = timezone(tz).localize(start_dt)
        cache.set(
            event_key,
            {
                'title': title,
                'start_dt': start_dt,
                'duration': duration,
            },
            3600
        )
        return jsonify(url=url_for_index(_external=True, _anchor=f'create-event:meeting::{event_key}'))

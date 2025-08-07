# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import timedelta

import pytz
from sqlalchemy import func, types
from sqlalchemy.sql import operators
from sqlalchemy.sql.sqltypes import Interval
from sqlalchemy.util import memoized_property


class UTCDateTime(types.TypeDecorator):
    impl = types.DateTime
    cache_ok = True

    class Comparator(types.DateTime.Comparator):
        def astimezone(self, tz):
            """Convert the datetime to a specific timezone.

            This is useful if you want e.g. to cast to Date afterwards
            but need a specific timezone instead of UTC.

            When accessing the value returned by this method in Python
            it will be a naive datetime object in the specified time
            zone.

            :param tz: A timezone name or tzinfo object.
            """
            tz = getattr(tz, 'zone', tz)
            return func.timezone(tz, func.timezone('UTC', self.expr))
    comparator_factory = Comparator

    @memoized_property
    def _expression_adaptations(self):
        # this ensures that `UTCDateTime + Interval` returns another
        # `UTCDateTime` and not just a `DateTime`
        return {
            operators.add: {
                Interval: UTCDateTime
            },
            operators.sub: {
                Interval: UTCDateTime,
                UTCDateTime: Interval,
                # not sure why the base DateTime is needed here, but without it the result is
                # handled as a UTCDateTime instead of an Interval...
                types.DateTime: Interval,
            }
        }

    def process_bind_param(self, value, engine):
        if value is not None:
            if isinstance(value, timedelta):
                # XXX don't ask me why this goes through here... but without it, querying something like
                # `Event.end_dt + timedelta(hours=1)` fails
                return value
            return value.astimezone(pytz.utc).replace(tzinfo=None)

    def process_result_value(self, value, engine):
        if value is not None:
            return value.replace(tzinfo=pytz.utc)

    def alembic_render_type(self, autogen_context, toplevel_code):
        autogen_context.imports.add('from indico.core.db.sqlalchemy import UTCDateTime')
        return type(self).__name__

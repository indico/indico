# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytz
from sqlalchemy import func, types
from sqlalchemy.sql import operators
from sqlalchemy.sql.sqltypes import Interval
from sqlalchemy.util import memoized_property


class UTCDateTime(types.TypeDecorator):
    impl = types.DateTime

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
                UTCDateTime: Interval
            }
        }

    def process_bind_param(self, value, engine):
        if value is not None:
            return value.astimezone(pytz.utc).replace(tzinfo=None)

    def process_result_value(self, value, engine):
        if value is not None:
            return value.replace(tzinfo=pytz.utc)

    def alembic_render_type(self, autogen_context, toplevel_code):
        autogen_context.imports.add('from indico.core.db.sqlalchemy import UTCDateTime')
        return type(self).__name__

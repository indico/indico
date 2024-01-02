# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.series.controllers import RHEventSeries
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('event_series', __name__, url_prefix='/event-series')

_bp.add_url_rule('/<int:series_id>', 'event_series', RHEventSeries, methods=('GET', 'PATCH', 'DELETE'))
_bp.add_url_rule('/', 'event_series', RHEventSeries, methods=('POST',))

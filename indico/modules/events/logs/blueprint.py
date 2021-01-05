# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.logs.controllers import RHEventLogs, RHEventLogsJSON
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('event_logs', __name__, template_folder='templates', virtual_template_folder='events/logs',
                      url_prefix='/event/<confId>/manage/logs')

_bp.add_url_rule('/', 'index', RHEventLogs)
_bp.add_url_rule('/api/logs', 'logs', RHEventLogsJSON)

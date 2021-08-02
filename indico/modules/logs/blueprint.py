# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.logs.controllers import RHEventLogs, RHEventLogsJSON
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('logs', __name__, template_folder='templates', virtual_template_folder='logs',
                      url_prefix='/event/<int:event_id>/manage/logs')

_bp.add_url_rule('/', 'event', RHEventLogs)
_bp.add_url_rule('/api/logs', 'api_event_logs', RHEventLogsJSON)

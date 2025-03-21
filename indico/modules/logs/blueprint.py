# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import request

from indico.modules.logs.controllers import (RHCategoryLogs, RHCategoryLogsJSON, RHEventLogs, RHEventLogsJSON,
                                             RHUserLogs, RHUserLogsJSON)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('logs', __name__, template_folder='templates', virtual_template_folder='logs')

# Events
_bp.add_url_rule('/event/<int:event_id>/manage/logs/', 'event', RHEventLogs)
_bp.add_url_rule('/event/<int:event_id>/manage/logs/api/logs', 'api_event_logs', RHEventLogsJSON)

# Categories
_bp.add_url_rule('/category/<int:category_id>/manage/logs/', 'category', RHCategoryLogs)
_bp.add_url_rule('/category/<int:category_id>/manage/logs/api/logs', 'api_category_logs', RHCategoryLogsJSON)

# Users
with _bp.add_prefixed_rules('/user/<int:user_id>', '/user'):
    _bp.add_url_rule('/logs/', 'user', RHUserLogs)
    _bp.add_url_rule('/logs/api/logs', 'api_user_logs', RHUserLogsJSON)


@_bp.url_defaults
def _add_user_id(endpoint, values):
    if endpoint in {'logs.user', 'logs.api_user_logs'} and 'user_id' not in values:
        values['user_id'] = request.view_args.get('user_id')

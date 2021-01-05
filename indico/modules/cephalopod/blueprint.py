# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.cephalopod.controllers import RHCephalopod, RHCephalopodSync, RHSystemInfo
from indico.web.flask.wrappers import IndicoBlueprint


cephalopod_blueprint = _bp = IndicoBlueprint('cephalopod', __name__, template_folder='templates',
                                             virtual_template_folder='cephalopod')

_bp.add_url_rule('/admin/community-hub/', 'index', RHCephalopod, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/community-hub/sync', 'sync', RHCephalopodSync, methods=('POST',))
_bp.add_url_rule('/system-info', 'system-info', RHSystemInfo)

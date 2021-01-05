# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.plugins.controllers import RHPluginDetails, RHPlugins
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('plugins', __name__, template_folder='templates', virtual_template_folder='plugins',
                      url_prefix='/admin/plugins')

_bp.add_url_rule('/', 'index', RHPlugins)
_bp.add_url_rule('/<plugin>/', 'details', RHPluginDetails, methods=('GET', 'POST'))

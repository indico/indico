# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.bootstrap.controllers import RHBootstrap
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('bootstrap', __name__, template_folder='templates', virtual_template_folder='bootstrap')
_bp.add_url_rule('/bootstrap', 'index', RHBootstrap, methods=('GET', 'POST'))

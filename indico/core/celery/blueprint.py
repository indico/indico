# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.celery.controllers import RHCeleryTasks
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('celery', __name__, url_prefix='/admin/tasks', template_folder='templates',
                      virtual_template_folder='celery')

_bp.add_url_rule('/', 'index', RHCeleryTasks)

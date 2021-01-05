# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.features.controllers import RHFeatures, RHSwitchFeature
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('event_features', __name__, template_folder='templates',
                      virtual_template_folder='events/features', url_prefix='/event/<confId>/manage/features')

_bp.add_url_rule('/', 'index', RHFeatures)
_bp.add_url_rule('/<feature>', 'switch', RHSwitchFeature, methods=('PUT', 'DELETE'))

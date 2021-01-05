# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.legal.controllers import RHDisplayPrivacyPolicy, RHDisplayTOS, RHManageLegalMessages
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('legal', __name__, template_folder='templates', virtual_template_folder='legal')

_bp.add_url_rule('/admin/legal', 'manage', RHManageLegalMessages, methods=('GET', 'POST'))
_bp.add_url_rule('/tos', 'display_tos', RHDisplayTOS)
_bp.add_url_rule('/privacy', 'display_privacy', RHDisplayPrivacyPolicy)

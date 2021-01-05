# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.announcement.controllers import RHAnnouncement
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('announcement', __name__, template_folder='templates', virtual_template_folder='announcement')

_bp.add_url_rule('/admin/announcement', 'manage', RHAnnouncement, methods=('GET', 'POST'))

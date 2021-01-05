# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.static.controllers import RHStaticSiteBuild, RHStaticSiteDownload, RHStaticSiteList
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('static_site', __name__, template_folder='templates', virtual_template_folder='events/static',
                      url_prefix='/event/<confId>/manage/offline-copy')

# Event management
_bp.add_url_rule('/', 'list', RHStaticSiteList)
_bp.add_url_rule('/<int:id>.zip', 'download', RHStaticSiteDownload)
_bp.add_url_rule('/build', 'build', RHStaticSiteBuild, methods=('POST',))

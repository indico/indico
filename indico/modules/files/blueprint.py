# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.files.controllers import RHDeleteFile, RHFileDownload, RHFileInfo
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('files', __name__)

_bp.add_url_rule('/files/<uuid:uuid>', 'file_info', RHFileInfo)
_bp.add_url_rule('/files/<uuid:uuid>/download', 'download_file', RHFileDownload)
_bp.add_url_rule('/files/<uuid:uuid>', 'delete_file', RHDeleteFile, methods=('DELETE',))

# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from werkzeug.exceptions import Forbidden

from indico.core.config import config
from indico.modules.admin import RHAdminBase
from indico.modules.dev.views import WPDev
from indico.modules.files.controllers import UploadFileMixin


class RHDevBase(RHAdminBase):
    """Base class for all dev-only RHs."""

    def _check_access(self):
        RHAdminBase._check_access(self)
        if not config.DEBUG:
            raise Forbidden('Debug mode is disabled')


class RHReactFields(RHDevBase):
    def _process(self):
        return WPDev.render_template('react_fields.html')


class RHTestUpload(UploadFileMixin, RHDevBase):
    def get_file_context(self):
        return ('dev',)

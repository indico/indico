# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.dev.controllers import RHReactFields, RHTestUpload
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('dev', __name__, template_folder='templates', virtual_template_folder='dev')

_bp.add_url_rule('/dev/react/fields', 'react_fields', RHReactFields)
_bp.add_url_rule('/dev/upload', 'test_upload', RHTestUpload, methods=('POST',))

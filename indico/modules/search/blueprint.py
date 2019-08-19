# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.search.controllers import RHSearch
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('search', __name__, template_folder='templates', virtual_template_folder='search')

_bp.add_url_rule('/search/', 'search', RHSearch)

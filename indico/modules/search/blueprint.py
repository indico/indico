# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.search.controllers import RHAPISearch, RHAPISearchPlaceholders, RHSearchDisplay
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('search', __name__, template_folder='templates', virtual_template_folder='search')

# Frontend
_bp.add_url_rule('/search/', 'search', RHSearchDisplay)

# Search APIs
_bp.add_url_rule('/search/api/placeholders', 'api_search_placeholders', RHAPISearchPlaceholders)
_bp.add_url_rule('/search/api/search', 'api_search', RHAPISearch)

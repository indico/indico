# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.search.controllers import (RHSearch, RHSearchCategories, RHSearchContributions, RHSearchEvents,
                                               RHSearchFiles)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('search', __name__, template_folder='templates', virtual_template_folder='search')

# Frontend
_bp.add_url_rule('/search/', 'search', RHSearch)

# Search APIs
_bp.add_url_rule('/search/api/categories', 'search_categories', RHSearchCategories)
_bp.add_url_rule('/search/api/events', 'search_events', RHSearchEvents)
_bp.add_url_rule('/search/api/contributions', 'search_contributions', RHSearchContributions)
_bp.add_url_rule('/search/api/files', 'search_files', RHSearchFiles)

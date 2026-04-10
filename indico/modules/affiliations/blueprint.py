# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.affiliations.controllers import (RHAffiliationAPI, RHAffiliationsAPI, RHAffiliationsDashboard,
                                                     RHAffiliationsMapping, RHAffiliationsMappingAPI,
                                                     RHAffiliationsMappingApplyAPI, RHAffiliationsMappingStatusAPI,
                                                     RHCountries, RHSearchAffiliations)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('affiliations', __name__, template_folder='templates', virtual_template_folder='affiliations',
                      url_prefix='/affiliations')

# Affiliations
_bp.add_url_rule('!/admin/affiliations', 'dashboard', RHAffiliationsDashboard)
_bp.add_url_rule('!/admin/affiliations/mapping', 'mapping', RHAffiliationsMapping)
_bp.add_url_rule('!/api/admin/affiliations', 'api_admin_affiliations', RHAffiliationsAPI, methods=('GET', 'POST'))
_bp.add_url_rule('!/api/admin/affiliations/mapping', 'api_admin_affiliations_mapping', RHAffiliationsMappingAPI,
                 methods=('GET', 'POST'))
_bp.add_url_rule('!/api/admin/affiliations/mapping/status/<task_id>', 'api_admin_affiliations_mapping_status',
                 RHAffiliationsMappingStatusAPI, methods=('GET',))
_bp.add_url_rule('!/api/admin/affiliations/mapping/apply', 'api_admin_affiliations_mapping_apply',
                 RHAffiliationsMappingApplyAPI, methods=('POST',))
_bp.add_url_rule('!/api/admin/affiliations/<int:affiliation_id>', 'api_admin_affiliation', RHAffiliationAPI,
                 methods=('GET', 'PATCH', 'DELETE'))
_bp.add_url_rule('!/api/countries', 'api_countries', RHCountries)
_bp.add_url_rule('!/api/affiliations/', 'api_affiliations', RHSearchAffiliations)

# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from indico.modules.events.contributions.controllers import (RHContributions, RHCreateContribution,
                                                             RHEditContribution, RHContributionREST,
                                                             RHDeleteContributions, RHContributionPersonList,
                                                             RHContributionProtection, RHContributionsReportCustomize,
                                                             RHContributionsReportStaticURL,
                                                             RHContributionSubContributions, RHCreateSubContribution,
                                                             RHEditSubContribution, RHSubContributionREST,
                                                             RHDeleteSubContributions, RHContributionUpdateStartDate,
                                                             RHContributionUpdateDuration,
                                                             RHContributionsMaterialPackage)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('contributions', __name__, template_folder='templates',
                      virtual_template_folder='events/contributions', url_prefix='/event/<confId>')

_bp.add_url_rule('/manage/contributions/', 'manage_contributions', RHContributions)
_bp.add_url_rule('/manage/contributions/customize', 'customize_contrib_report',
                 RHContributionsReportCustomize, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/contributions/static-url', 'generate_static_url', RHContributionsReportStaticURL,
                 methods=('POST',))
_bp.add_url_rule('/manage/contributions/create',
                 'manage_create_contrib', RHCreateContribution, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/contributions/delete',
                 'manage_delete_contribs', RHDeleteContributions, methods=('POST',))
_bp.add_url_rule('/manage/contributions/person-list', 'person_list', RHContributionPersonList, methods=('POST',))
_bp.add_url_rule('/manage/contributions/material-package', 'material_package', RHContributionsMaterialPackage,
                 methods=('POST',))

# Single contribution
_bp.add_url_rule('/manage/contributions/<int:contrib_id>',
                 'manage_contrib_rest', RHContributionREST, methods=('DELETE', 'PATCH'))
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/edit',
                 'manage_update_contrib', RHEditContribution, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/protection', 'manage_contrib_protection',
                 RHContributionProtection, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/start-date', 'manage_start_date',
                 RHContributionUpdateStartDate, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/duration', 'manage_duration', RHContributionUpdateDuration,
                 methods=('GET', 'POST'))

# Subcontributions
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/subcontributions/', 'manage_subcontributions',
                 RHContributionSubContributions)
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/subcontributions/delete', 'manage_delete_subcontribs',
                 RHDeleteSubContributions, methods=('POST',))
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/subcontributions/create', 'manage_create_subcontrib',
                 RHCreateSubContribution, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/subcontributions/<int:subcontrib_id>',
                 'manage_subcontrib_rest', RHSubContributionREST, methods=('DELETE',))
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/subcontributions/<int:subcontrib_id>/edit',
                 'manage_edit_subcontrib', RHEditSubContribution, methods=('GET', 'POST'))

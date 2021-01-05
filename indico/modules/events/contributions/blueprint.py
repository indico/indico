# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from functools import partial

from indico.modules.events.contributions.controllers import display, management
from indico.modules.events.contributions.controllers.compat import compat_contribution, compat_subcontribution
from indico.web.flask.util import make_compat_redirect_func
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('contributions', __name__, template_folder='templates',
                      virtual_template_folder='events/contributions', url_prefix='/event/<confId>')

_bp.add_url_rule('/manage/contributions/', 'manage_contributions', management.RHContributions)
_bp.add_url_rule('/manage/contributions/customize', 'customize_contrib_list',
                 management.RHContributionListCustomize, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/contributions/static-url', 'generate_static_url', management.RHContributionListStaticURL,
                 methods=('POST',))
_bp.add_url_rule('/manage/contributions/create', 'manage_create_contrib', management.RHCreateContribution,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/contributions/delete', 'manage_delete_contribs', management.RHDeleteContributions,
                 methods=('POST',))
_bp.add_url_rule('/manage/contributions/person-list', 'person_list', management.RHContributionPersonList,
                 methods=('POST',))
_bp.add_url_rule('/manage/contributions/material-package', 'material_package',
                 management.RHContributionsMaterialPackage, methods=('POST',))
_bp.add_url_rule('/manage/contributions/contributions.csv', 'contributions_csv_export',
                 management.RHContributionsExportCSV, methods=('POST',))
_bp.add_url_rule('/manage/contributions/contributions.xlsx', 'contributions_excel_export',
                 management.RHContributionsExportExcel, methods=('POST',))
_bp.add_url_rule('/manage/contributions/contributions.pdf', 'contributions_pdf_export',
                 management.RHContributionsExportPDF, methods=('POST',))
_bp.add_url_rule('/manage/contributions/contributions.zip', 'contributions_tex_export',
                 management.RHContributionsExportTeX, methods=('POST',))

# LaTeX-based exports
_bp.add_url_rule('/manage/contributions/tex-export/<uuid>', 'contributions_tex_export_book',
                 management.RHContributionsExportTeXBook)
_bp.add_url_rule('/manage/contributions/tex-export-dialog', 'contributions_tex_export_dialog',
                 management.RHContributionExportTexConfig, methods=('POST',))

# Import
_bp.add_url_rule('/manage/contributions/import', 'contributions_import',
                 management.RHContributionsImportCSV, methods=('GET', 'POST'))

# Single contribution
_bp.add_url_rule('/manage/contributions/<int:contrib_id>', 'manage_contrib_rest', management.RHContributionREST,
                 methods=('DELETE', 'PATCH'))
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/edit', 'manage_update_contrib',
                 management.RHEditContribution, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/protection', 'manage_contrib_protection',
                 management.RHContributionProtection, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/start-date', 'manage_start_date',
                 management.RHContributionUpdateStartDate, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/duration', 'manage_duration',
                 management.RHContributionUpdateDuration, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/acl', 'acl', management.RHContributionACL)
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/acl-message', 'acl_message',
                 management.RHContributionACLMessage)
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/clone', 'clone_contribution', management.RHCloneContribution,
                 methods=('POST',))

# Contribution RESTful endpoints
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/references/', 'create_contrib_reference_rest',
                 management.RHCreateContributionReferenceREST, methods=('POST',))

# Subcontributions
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/subcontributions/', 'manage_subcontributions',
                 management.RHContributionSubContributions)
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/subcontributions/delete', 'manage_delete_subcontribs',
                 management.RHDeleteSubContributions, methods=('POST',))
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/subcontributions/create', 'manage_create_subcontrib',
                 management.RHCreateSubContribution, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/subcontributions/sort', 'sort_subcontributions',
                 management.RHSortSubContributions, methods=('POST',))
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/subcontributions/<int:subcontrib_id>/edit',
                 'manage_edit_subcontrib', management.RHEditSubContribution, methods=('GET', 'POST'))

# Subcontributions RESTful endpoints
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/subcontributions/',
                 'create_subcontrib_rest', management.RHCreateSubContributionREST, methods=('POST',))
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/subcontributions/<int:subcontrib_id>',
                 'manage_subcontrib_rest', management.RHSubContributionREST, methods=('DELETE',))
_bp.add_url_rule('/manage/contributions/<int:contrib_id>/subcontributions/<int:subcontrib_id>/references/',
                 'create_subcontrib_reference_rest', management.RHCreateSubContributionReferenceREST, methods=('POST',))

# Contribution types
_bp.add_url_rule('/manage/contributions/types/', 'manage_types', management.RHManageContributionTypes)
_bp.add_url_rule('/manage/contributions/types/create', 'create_type', management.RHCreateContributionType,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/contributions/types/<int:contrib_type_id>', 'manage_type', management.RHEditContributionType,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/contributions/types/<int:contrib_type_id>/delete', 'delete_type',
                 management.RHDeleteContributionType, methods=('POST',))

# Default contribution duration
_bp.add_url_rule('/manage/contributions/duration', 'manage_default_duration',
                 management.RHManageDefaultContributionDuration, methods=('GET', 'POST'))

# Publish contribution
_bp.add_url_rule('/manage/contributions/published', 'manage_publication',
                 management.RHManageContributionPublicationREST, methods=('GET', 'PUT', 'DELETE'))

# Custom contribution fields
_bp.add_url_rule('/manage/contributions/fields/', 'manage_fields', management.RHManageContributionFields)
_bp.add_url_rule('/manage/contributions/fields/create/<field_type>', 'create_field',
                 management.RHCreateContributionField, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/contributions/fields/<int:contrib_field_id>', 'manage_field',
                 management.RHEditContributionField, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/contributions/fields/<int:contrib_field_id>/delete', 'delete_field',
                 management.RHDeleteContributionField, methods=('POST',))
_bp.add_url_rule('/manage/contributions/fields/sort', 'sort_fields', management.RHSortContributionFields,
                 methods=('POST',))
_bp.add_url_rule('/manage/contributions/fields/description', 'manage_description_field',
                 management.RHManageDescriptionField, methods=('GET', 'POST'))

# Display
_bp.add_url_rule('/contributions/', 'contribution_list', display.RHContributionList)
_bp.add_url_rule('/contributions/contributions.pdf', 'contribution_list_pdf', display.RHContributionsExportToPDF)
_bp.add_url_rule('/contributions/mine', 'my_contributions', display.RHMyContributions)
_bp.add_url_rule('/contributions/authors', 'author_list', display.RHAuthorList)
_bp.add_url_rule('/contributions/speakers', 'speaker_list', display.RHSpeakerList)
_bp.add_url_rule('/contributions/customize', 'customize_contribution_list', display.RHContributionListFilter,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/contributions/static-url', 'contribution_list_static_url',
                 display.RHContributionListDisplayStaticURL, methods=('POST',))
_bp.add_url_rule('/contributions/<int:contrib_id>/', 'display_contribution', display.RHContributionDisplay)
_bp.add_url_rule('/contributions/<int:contrib_id>/author/<int:person_id>', 'display_author',
                 display.RHContributionAuthor)
_bp.add_url_rule('/contributions/<int:contrib_id>/contribution.pdf', 'export_pdf', display.RHContributionExportToPDF)
_bp.add_url_rule('/contributions/<int:contrib_id>/contribution.ics', 'export_ics', display.RHContributionExportToICAL)
_bp.add_url_rule('/contributions/<int:contrib_id>/subcontributions/<int:subcontrib_id>', 'display_subcontribution',
                 display.RHSubcontributionDisplay)

# Legacy URLs
_compat_bp = IndicoBlueprint('compat_contributions', __name__, url_prefix='/event/<event_id>')

with _compat_bp.add_prefixed_rules('/session/<legacy_session_id>'):
    _compat_bp.add_url_rule('/contribution/<legacy_contribution_id>', 'contribution',
                            partial(compat_contribution, 'display_contribution'))
    _compat_bp.add_url_rule('/contribution/<legacy_contribution_id>.ics', 'contribution_ics',
                            partial(compat_contribution, 'export_ics'))
    _compat_bp.add_url_rule('/contribution/<legacy_contribution_id>.pdf', 'contribution_pdf',
                            partial(compat_contribution, 'export_pdf'))
    _compat_bp.add_url_rule('/contribution/<legacy_contribution_id>/<legacy_subcontribution_id>',
                            'subcontribution', compat_subcontribution)

_compat_bp.add_url_rule('/my-conference/contributions', 'my_contributions',
                        make_compat_redirect_func(_bp, 'my_contributions', view_args_conv={'event_id': 'confId'}))

_compat_bp.add_url_rule('!/contributionDisplay.py', 'contribution_modpython',
                        make_compat_redirect_func(_compat_bp, 'contribution',
                                                  view_args_conv={'confId': 'event_id',
                                                                  'contribId': 'legacy_contribution_id'}))
_compat_bp.add_url_rule('!/subContributionDisplay.py', 'subcontribution_modpython',
                        make_compat_redirect_func(_compat_bp, 'subcontribution',
                                                  view_args_conv={'confId': 'event_id',
                                                                  'contribId': 'legacy_contribution_id',
                                                                  'subContId': 'legacy_subcontribution_id'}))

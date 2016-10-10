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

from indico.modules.events.abstracts.controllers.display import RHDisplayAbstract, RHDisplayAbstractExportPDF
from indico.modules.events.abstracts.controllers.email_templates import (RHAddEmailTemplate, RHEditEmailTemplateRules,
                                                                         RHEditEmailTemplateText, RHEmailTemplateList,
                                                                         RHDeleteEmailTemplate, RHPreviewEmailTemplate,
                                                                         RHSortEmailTemplates)
from indico.modules.events.abstracts.controllers.management import (RHAbstracts, RHManageBOA, RHAbstractList,
                                                                    RHAbstractListCustomize, RHAbstractListStaticURL,
                                                                    RHManageAbstractSubmission, RHManageAbstract,
                                                                    RHManageAbstractReviewing, RHCreateAbstract,
                                                                    RHDeleteAbstracts, RHAbstractPersonList,
                                                                    RHAbstractsDownloadAttachments,
                                                                    RHAbstractsExportPDF, RHAbstractExportPDF,
                                                                    RHAbstractsExportCSV, RHAbstractsExportExcel)
from indico.web.flask.wrappers import IndicoBlueprint

_bp = IndicoBlueprint('abstracts', __name__, url_prefix='/event/<confId>', template_folder='templates',
                      virtual_template_folder='events/abstracts')

# Display pages
_bp.add_url_rule('/abstracts/<int:abstract_id>/', 'display_abstract', RHDisplayAbstract)
_bp.add_url_rule('/abstracts/<int:abstract_id>/abstract.pdf', 'display_abstract_pdf_export', RHDisplayAbstractExportPDF)

# Management
_bp.add_url_rule('/manage/abstracts/', 'manage_abstracts', RHAbstracts)
_bp.add_url_rule('/manage/abstracts/boa', 'manage_boa', RHManageBOA, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/settings', 'manage_submission_settings', RHManageAbstractSubmission,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/review-settings', 'manage_reviewing_settings', RHManageAbstractReviewing,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/list/', 'manage_abstract_list', RHAbstractList)
_bp.add_url_rule('/manage/abstracts/list/customize', 'customize_abstract_list', RHAbstractListCustomize,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/abstracts.pdf', 'abstracts_pdf_export', RHAbstractsExportPDF,
                 methods=('POST',))
_bp.add_url_rule('/manage/abstracts/abstracts.csv', 'abstracts_csv_export', RHAbstractsExportCSV,
                 methods=('POST',))
_bp.add_url_rule('/manage/abstracts/abstracts.xlsx', 'abstracts_xlsx_export', RHAbstractsExportExcel,
                 methods=('POST',))
_bp.add_url_rule('/manage/abstracts/create', 'manage_create_abstract', RHCreateAbstract, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/delete', 'manage_delete_abstracts', RHDeleteAbstracts, methods=('POST',))
_bp.add_url_rule('/manage/abstracts/person-list', 'person_list', RHAbstractPersonList, methods=('POST',))
_bp.add_url_rule('/manage/abstracts/attachments', 'download_attachments', RHAbstractsDownloadAttachments,
                 methods=('POST',))
_bp.add_url_rule('/manage/abstracts/list/static-url', 'generate_static_url', RHAbstractListStaticURL, methods=('POST',))

# E-mail templates
_bp.add_url_rule('/manage/abstracts/email-templates/', 'email_tpl_list', RHEmailTemplateList)
_bp.add_url_rule('/manage/abstracts/email-templates/add', 'email_tpl_add', RHAddEmailTemplate, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/email-templates/sort', 'email_tpl_sort', RHSortEmailTemplates, methods=('POST',))
_bp.add_url_rule('/manage/abstracts/email-templates/<email_tpl_id>', 'email_tpl_delete', RHDeleteEmailTemplate,
                 methods=('DELETE',))
_bp.add_url_rule('/manage/abstracts/email-templates/<email_tpl_id>/edit', 'email_tpl_rule_edit',
                 RHEditEmailTemplateRules, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/email-templates/<email_tpl_id>/edit-text', 'email_tpl_text_edit',
                 RHEditEmailTemplateText, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/email-templates/<email_tpl_id>/preview', 'email_tpl_preview',
                 RHPreviewEmailTemplate)

# Abstract-specific management
_bp.add_url_rule('/manage/abstracts/<int:abstract_id>/', 'manage_abstract', RHManageAbstract)
_bp.add_url_rule('/manage/abstracts/<int:abstract_id>/abstract.pdf', 'manage_abstract_pdf_export', RHAbstractExportPDF)

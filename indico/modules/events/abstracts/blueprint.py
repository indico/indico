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

from indico.modules.events.abstracts.controllers import boa, common, display, email_templates, management, reviewing
from indico.web.flask.util import make_compat_redirect_func
from indico.web.flask.wrappers import IndicoBlueprint

_bp = IndicoBlueprint('abstracts', __name__, url_prefix='/event/<confId>', template_folder='templates',
                      virtual_template_folder='events/abstracts')

# Display pages
_bp.add_url_rule('/abstracts/<int:abstract_id>/', 'display_abstract', display.RHDisplayAbstract)
_bp.add_url_rule('/abstracts/<int:abstract_id>/notifications', 'notification_log', management.RHAbstractNotificationLog)
_bp.add_url_rule('/abstracts/<int:abstract_id>/abstract.pdf', 'display_abstract_pdf_export',
                 display.RHDisplayAbstractExportPDF)
_bp.add_url_rule('/abstracts/<int:abstract_id>/attachments/<file_id>/<filename>', 'download_attachment',
                 reviewing.RHAbstractsDownloadAttachment)
_bp.add_url_rule('/abstracts/mine', 'my_abstracts', display.RHMyAbstracts)
_bp.add_url_rule('/abstracts/mine.pdf', 'my_abstracts_pdf', display.RHMyAbstractsExportPDF)
_bp.add_url_rule('/abstracts/submit', 'submit', display.RHSubmitAbstract, methods=('GET', 'POST'))

# Reviewing pages (display area)
_bp.add_url_rule('/call-for-abstracts/reviewing/', 'display_reviewable_tracks', reviewing.RHDisplayReviewableTracks)
_bp.add_url_rule('/call-for-abstracts/reviewing/<int:track_id>/', 'display_reviewable_track_abstracts',
                 reviewing.RHDisplayReviewableTrackAbstracts)
_bp.add_url_rule('/call-for-abstracts/reviewing/<int:track_id>/customize', 'display_customize_abstract_list',
                 reviewing.RHDisplayAbstractListCustomize, methods=('GET', 'POST'))
_bp.add_url_rule('/call-for-abstracts/reviewing/<int:track_id>/attachments', 'display_download_attachments',
                 reviewing.RHDisplayAbstractsDownloadAttachments, methods=('POST',))
_bp.add_url_rule('/call-for-abstracts/reviewing/<int:track_id>/abstracts.pdf', 'display_abstracts_pdf_export',
                 reviewing.RHDisplayAbstractsExportPDF, methods=('POST',))
_bp.add_url_rule('/call-for-abstracts/reviewing/<int:track_id>/abstracts.csv', 'display_abstracts_csv_export',
                 reviewing.RHDisplayAbstractsExportCSV, methods=('POST',))
_bp.add_url_rule('/call-for-abstracts/reviewing/<int:track_id>/abstracts.xlsx', 'display_abstracts_xlsx_export',
                 reviewing.RHDisplayAbstractsExportExcel, methods=('POST',))

# Book of Abstracts
_bp.add_url_rule('/manage/abstracts/boa', 'manage_boa', boa.RHManageBOA, methods=('GET', 'POST'))
_bp.add_url_rule('/book-of-abstracts.pdf', 'export_boa', boa.RHExportBOA)

_bp.add_url_rule('/abstracts/other-list', 'other_abstracts', reviewing.RHListOtherAbstracts, methods=('POST',))

# Management
_bp.add_url_rule('/manage/abstracts/', 'manage_abstracts', management.RHAbstracts)
_bp.add_url_rule('/manage/abstracts/schedule', 'schedule_abstracts_call', management.RHScheduleCFA,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/open', 'open_abstracts_call', management.RHOpenCFA, methods=('POST',))
_bp.add_url_rule('/manage/abstracts/close', 'close_abstracts_call', management.RHCloseCFA, methods=('POST',))
_bp.add_url_rule('/manage/abstracts/settings', 'manage_submission_settings', management.RHManageAbstractSubmission,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/review-settings', 'manage_reviewing_settings', management.RHManageAbstractReviewing,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/teams', 'manage_reviewing_roles', management.RHManageReviewingRoles,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/list/', 'manage_abstract_list', management.RHAbstractList)
_bp.add_url_rule('/manage/abstracts/list/customize', 'customize_abstract_list', management.RHAbstractListCustomize,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/abstracts.pdf', 'abstracts_pdf_export', management.RHAbstractsExportPDF,
                 methods=('POST',))
_bp.add_url_rule('/manage/abstracts/abstracts.csv', 'abstracts_csv_export', management.RHAbstractsExportCSV,
                 methods=('POST',))
_bp.add_url_rule('/manage/abstracts/abstracts.xlsx', 'abstracts_xlsx_export', management.RHAbstractsExportExcel,
                 methods=('POST',))
_bp.add_url_rule('/manage/abstracts/abstracts.json', 'abstracts_json_export', management.RHAbstractsExportJSON,
                 methods=('POST',))
_bp.add_url_rule('/manage/abstracts/create', 'manage_create_abstract', management.RHCreateAbstract,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/delete', 'manage_delete_abstracts', management.RHDeleteAbstracts, methods=('POST',))
_bp.add_url_rule('/manage/abstracts/person-list', 'person_list', management.RHAbstractPersonList, methods=('POST',))
_bp.add_url_rule('/manage/abstracts/attachments', 'download_attachments', management.RHAbstractsDownloadAttachments,
                 methods=('POST',))
_bp.add_url_rule('/manage/abstracts/judge', 'manage_judge_abstracts', management.RHBulkAbstractJudgment,
                 methods=('POST',))
_bp.add_url_rule('/manage/abstracts/list/static-url', 'generate_static_url', management.RHAbstractListStaticURL,
                 methods=('POST',))

# E-mail templates
_bp.add_url_rule('/manage/abstracts/email-templates/', 'email_tpl_list', email_templates.RHEmailTemplateList)
_bp.add_url_rule('/manage/abstracts/email-templates/add',
                 'email_tpl_add', email_templates.RHAddEmailTemplate, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/email-templates/sort',
                 'email_tpl_sort', email_templates.RHSortEmailTemplates, methods=('POST',))
_bp.add_url_rule('/manage/abstracts/email-templates/<email_tpl_id>',
                 'email_tpl_delete', email_templates.RHDeleteEmailTemplate, methods=('DELETE',))
_bp.add_url_rule('/manage/abstracts/email-templates/<email_tpl_id>/edit',
                 'email_tpl_rule_edit', email_templates.RHEditEmailTemplateRules, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/email-templates/<email_tpl_id>/edit-text',
                 'email_tpl_text_edit', email_templates.RHEditEmailTemplateText, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/email-templates/<email_tpl_id>',
                 'email_tpl_rest', email_templates.RHEmailTemplateREST, methods=('PATCH',))

# Abstract-specific management
_bp.add_url_rule('/manage/abstracts/<int:abstract_id>/', 'manage_abstract', management.RHManageAbstract,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/<int:abstract_id>/abstract.pdf', 'manage_abstract_pdf_export',
                 management.RHAbstractExportPDF)

# Abstract-specific
_bp.add_url_rule('/manage/abstracts/<int:abstract_id>/comment',
                 'comment_abstract', reviewing.RHSubmitAbstractComment, methods=('POST',))
_bp.add_url_rule('/manage/abstracts/<int:abstract_id>/comments/<int:comment_id>',
                 'edit_abstract_comment', reviewing.RHEditAbstractComment, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/<int:abstract_id>/comments/<int:comment_id>',
                 'delete_abstract_comment', reviewing.RHDeleteAbstractComment, methods=('DELETE',))

for prefix in ('/manage/abstracts', '/abstracts'):
    defaults = {'management': prefix != '/abstracts'}
    _bp.add_url_rule(prefix + '/<int:abstract_id>/edit', 'edit_abstract',
                     common.RHEditAbstract, methods=('GET', 'POST'), defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/withdraw', 'withdraw_abstract',
                     reviewing.RHWithdrawAbstract, methods=('POST',), defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/reset', 'reset_abstract_state',
                     reviewing.RHResetAbstractState, methods=('POST',), defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/abstract.pdf', 'manage_abstract_pdf_export',
                     management.RHAbstractExportPDF, defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/review/track/<int:track_id>', 'review_abstract',
                     reviewing.RHReviewAbstractForTrack, methods=('POST',), defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/judge', 'judge_abstract',
                     reviewing.RHJudgeAbstract, methods=('POST',), defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/reviewing-tracks', 'edit_review_tracks',
                     reviewing.RHEditReviewedForTrackList, methods=('POST',), defaults=defaults)


# Legacy URLs
_compat_bp = IndicoBlueprint('compat_abstracts', __name__, url_prefix='/event/<event_id>')
_compat_bp.add_url_rule('/call-for-abstracts/my-abstracts', 'my_abstracts',
                        make_compat_redirect_func(_bp, 'my_abstracts', view_args_conv={'event_id': 'confId'}))

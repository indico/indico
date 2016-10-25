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

from indico.modules.events.abstracts.controllers.boa import RHManageBOA, RHExportBOA
from indico.modules.events.abstracts.controllers.display import (RHDisplayAbstract, RHDisplayAbstractExportPDF,
                                                                 RHMyAbstracts, RHMyAbstractsExportPDF,
                                                                 RHSubmitAbstract)
from indico.modules.events.abstracts.controllers.email_templates import (RHAddEmailTemplate, RHEditEmailTemplateRules,
                                                                         RHEditEmailTemplateText, RHEmailTemplateList,
                                                                         RHDeleteEmailTemplate, RHSortEmailTemplates,
                                                                         RHEmailTemplateREST)
from indico.modules.events.abstracts.controllers.management import (RHAbstractList,
                                                                    RHAbstracts, RHAbstractListCustomize,
                                                                    RHAbstractListStaticURL,
                                                                    RHManageAbstractSubmission, RHManageAbstract,
                                                                    RHManageAbstractReviewing, RHCreateAbstract,
                                                                    RHDeleteAbstracts, RHAbstractPersonList,
                                                                    RHAbstractsDownloadAttachments,
                                                                    RHAbstractsExportPDF, RHAbstractExportPDF,
                                                                    RHAbstractsExportCSV, RHAbstractsExportExcel,
                                                                    RHAbstractsExportJSON,
                                                                    RHScheduleCFA, RHOpenCFA, RHCloseCFA,
                                                                    RHManageReviewingRoles, RHBulkAbstractJudgment,
                                                                    RHAbstractNotificationLog, RHEditAbstract)
from indico.modules.events.abstracts.controllers.reviewing import (RHAbstractsDownloadAttachment,
                                                                   RHResetAbstractState,
                                                                   RHWithdrawAbstract,
                                                                   RHLeaveComment,
                                                                   RHDeleteAbstractComment,
                                                                   RHEditAbstractComment,
                                                                   RHDisplayReviewableTracks,
                                                                   RHDisplayReviewableTrackAbstracts,
                                                                   RHListOtherAbstracts,
                                                                   RHReviewAbstractForTrack,
                                                                   RHJudgeAbstract,
                                                                   RHDisplayAbstractListCustomize,
                                                                   RHDisplayAbstractsExportPDF,
                                                                   RHDisplayAbstractsExportCSV,
                                                                   RHDisplayAbstractsExportExcel,
                                                                   RHDisplayAbstractsDownloadAttachments,
                                                                   RHEditReviewedForTrackList)
from indico.web.flask.util import make_compat_redirect_func
from indico.web.flask.wrappers import IndicoBlueprint

_bp = IndicoBlueprint('abstracts', __name__, url_prefix='/event/<confId>', template_folder='templates',
                      virtual_template_folder='events/abstracts')

# Display pages
_bp.add_url_rule('/abstracts/<int:abstract_id>/', 'display_abstract', RHDisplayAbstract)
_bp.add_url_rule('/abstracts/<int:abstract_id>/notifications', 'notification_log', RHAbstractNotificationLog)
_bp.add_url_rule('/abstracts/<int:abstract_id>/abstract.pdf', 'display_abstract_pdf_export', RHDisplayAbstractExportPDF)
_bp.add_url_rule('/abstracts/<int:abstract_id>/attachments/<file_id>/<filename>', 'download_attachment',
                 RHAbstractsDownloadAttachment)
_bp.add_url_rule('/abstracts/mine', 'my_abstracts', RHMyAbstracts)
_bp.add_url_rule('/abstracts/mine.pdf', 'my_abstracts_pdf', RHMyAbstractsExportPDF)
_bp.add_url_rule('/abstracts/submit', 'submit', RHSubmitAbstract, methods=('GET', 'POST'))

# Reviewing pages (display area)
_bp.add_url_rule('/call-for-abstracts/reviewing/', 'display_reviewable_tracks', RHDisplayReviewableTracks)
_bp.add_url_rule('/call-for-abstracts/reviewing/<int:track_id>/', 'display_reviewable_track_abstracts',
                 RHDisplayReviewableTrackAbstracts)
_bp.add_url_rule('/call-for-abstracts/reviewing/<int:track_id>/customize', 'display_customize_abstract_list',
                 RHDisplayAbstractListCustomize, methods=('GET', 'POST'))
_bp.add_url_rule('/call-for-abstracts/reviewing/<int:track_id>/attachments', 'display_download_attachments',
                 RHDisplayAbstractsDownloadAttachments, methods=('POST',))
_bp.add_url_rule('/call-for-abstracts/reviewing/<int:track_id>/abstracts.pdf', 'display_abstracts_pdf_export',
                 RHDisplayAbstractsExportPDF, methods=('POST',))
_bp.add_url_rule('/call-for-abstracts/reviewing/<int:track_id>/abstracts.csv', 'display_abstracts_csv_export',
                 RHDisplayAbstractsExportCSV, methods=('POST',))
_bp.add_url_rule('/call-for-abstracts/reviewing/<int:track_id>/abstracts.xlsx', 'display_abstracts_xlsx_export',
                 RHDisplayAbstractsExportExcel, methods=('POST',))

# Book of Abstracts
_bp.add_url_rule('/manage/abstracts/boa', 'manage_boa', RHManageBOA, methods=('GET', 'POST'))
_bp.add_url_rule('/book-of-abstracts.pdf', 'export_boa', RHExportBOA)

_bp.add_url_rule('/abstracts/other-list', 'other_abstracts', RHListOtherAbstracts, methods=('POST',))

# Management
_bp.add_url_rule('/manage/abstracts/', 'manage_abstracts', RHAbstracts)
_bp.add_url_rule('/manage/abstracts/schedule', 'schedule_abstracts_call', RHScheduleCFA, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/open', 'open_abstracts_call', RHOpenCFA, methods=('POST',))
_bp.add_url_rule('/manage/abstracts/close', 'close_abstracts_call', RHCloseCFA, methods=('POST',))
_bp.add_url_rule('/manage/abstracts/settings', 'manage_submission_settings', RHManageAbstractSubmission,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/review-settings', 'manage_reviewing_settings', RHManageAbstractReviewing,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/teams', 'manage_reviewing_roles', RHManageReviewingRoles, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/list/', 'manage_abstract_list', RHAbstractList)
_bp.add_url_rule('/manage/abstracts/list/customize', 'customize_abstract_list', RHAbstractListCustomize,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/abstracts.pdf', 'abstracts_pdf_export', RHAbstractsExportPDF,
                 methods=('POST',))
_bp.add_url_rule('/manage/abstracts/abstracts.csv', 'abstracts_csv_export', RHAbstractsExportCSV,
                 methods=('POST',))
_bp.add_url_rule('/manage/abstracts/abstracts.xlsx', 'abstracts_xlsx_export', RHAbstractsExportExcel,
                 methods=('POST',))
_bp.add_url_rule('/manage/abstracts/abstracts.json', 'abstracts_json_export', RHAbstractsExportJSON,
                 methods=('POST',))
_bp.add_url_rule('/manage/abstracts/create', 'manage_create_abstract', RHCreateAbstract, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/delete', 'manage_delete_abstracts', RHDeleteAbstracts, methods=('POST',))
_bp.add_url_rule('/manage/abstracts/person-list', 'person_list', RHAbstractPersonList, methods=('POST',))
_bp.add_url_rule('/manage/abstracts/attachments', 'download_attachments', RHAbstractsDownloadAttachments,
                 methods=('POST',))
_bp.add_url_rule('/manage/abstracts/judge', 'manage_judge_abstracts', RHBulkAbstractJudgment, methods=('POST',))
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
_bp.add_url_rule('/manage/abstracts/email-templates/<email_tpl_id>', 'email_tpl_rest',
                 RHEmailTemplateREST, methods=('PATCH',))

# Abstract-specific management
_bp.add_url_rule('/manage/abstracts/<int:abstract_id>/', 'manage_abstract', RHManageAbstract, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/<int:abstract_id>/abstract.pdf', 'manage_abstract_pdf_export', RHAbstractExportPDF)

# Abstract-specific
_bp.add_url_rule('/manage/abstracts/<int:abstract_id>/comment', 'comment_abstract', RHLeaveComment, methods=('POST',))
_bp.add_url_rule('/manage/abstracts/<int:abstract_id>/comments/<int:comment_id>',
                 'edit_abstract_comment', RHEditAbstractComment, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/<int:abstract_id>/comments/<int:comment_id>',
                 'delete_abstract_comment', RHDeleteAbstractComment, methods=('DELETE',))

for prefix in ('/manage/abstracts', '/abstracts'):
    defaults = {'management': prefix != '/abstracts'}
    _bp.add_url_rule(prefix + '/<int:abstract_id>/edit', 'edit_abstract',
                     RHEditAbstract, methods=('GET', 'POST'), defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/withdraw', 'withdraw_abstract',
                     RHWithdrawAbstract, methods=('POST',), defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/reset', 'reset_abstract_state',
                     RHResetAbstractState, methods=('POST',), defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/abstract.pdf', 'manage_abstract_pdf_export',
                     RHAbstractExportPDF, defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/review/track/<int:track_id>', 'review_abstract',
                     RHReviewAbstractForTrack, methods=('POST',), defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/judge', 'judge_abstract',
                     RHJudgeAbstract, methods=('POST',), defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/reviewing-tracks', 'edit_review_tracks',
                     RHEditReviewedForTrackList, methods=('POST',), defaults=defaults)

# Legacy URLs
_compat_bp = IndicoBlueprint('compat_abstracts', __name__, url_prefix='/event/<event_id>')
_compat_bp.add_url_rule('/call-for-abstracts/my-abstracts', 'my_abstracts',
                        make_compat_redirect_func(_bp, 'my_abstracts', view_args_conv={'event_id': 'confId'}))

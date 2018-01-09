# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from functools import partial

from flask import current_app, g

from indico.modules.events.abstracts.compat import compat_abstract
from indico.modules.events.abstracts.controllers import (abstract, abstract_list, boa, display, email_templates,
                                                         management, reviewing)
from indico.web.flask.util import make_compat_redirect_func
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('abstracts', __name__, url_prefix='/event/<confId>', template_folder='templates',
                      virtual_template_folder='events/abstracts')

# Display pages (not related to any specific abstract)
_bp.add_url_rule('/abstracts/', 'call_for_abstracts', display.RHCallForAbstracts)
_bp.add_url_rule('/abstracts/mine.pdf', 'my_abstracts_pdf', display.RHMyAbstractsExportPDF)
_bp.add_url_rule('/abstracts/submit', 'submit', display.RHSubmitAbstract, methods=('GET', 'POST'))

# Reviewing pages (display area, not related to any specific abstract)
_bp.add_url_rule('/abstracts/reviewing/', 'display_reviewable_tracks', reviewing.RHDisplayReviewableTracks)
_bp.add_url_rule('/abstracts/reviewing/<int:track_id>/', 'display_reviewable_track_abstracts',
                 reviewing.RHDisplayReviewableTrackAbstracts)
_bp.add_url_rule('/abstracts/reviewing/<int:track_id>/customize', 'display_customize_abstract_list',
                 reviewing.RHDisplayAbstractListCustomize, methods=('GET', 'POST'))
_bp.add_url_rule('/abstracts/reviewing/<int:track_id>/attachments', 'display_download_attachments',
                 reviewing.RHDisplayAbstractsDownloadAttachments, methods=('POST',))
_bp.add_url_rule('/abstracts/reviewing/<int:track_id>/abstracts.pdf', 'display_abstracts_pdf_export',
                 reviewing.RHDisplayAbstractsExportPDF, methods=('POST',))
_bp.add_url_rule('/abstracts/reviewing/<int:track_id>/abstracts.csv', 'display_abstracts_csv_export',
                 reviewing.RHDisplayAbstractsExportCSV, methods=('POST',))
_bp.add_url_rule('/abstracts/reviewing/<int:track_id>/abstracts.xlsx', 'display_abstracts_xlsx_export',
                 reviewing.RHDisplayAbstractsExportExcel, methods=('POST',))

# Book of Abstracts
_bp.add_url_rule('/manage/abstracts/boa', 'manage_boa', boa.RHManageBOA, methods=('GET', 'POST'))
_bp.add_url_rule('/book-of-abstracts.pdf', 'export_boa', boa.RHExportBOA)

# Misc
_bp.add_url_rule('/abstracts/other-list', 'other_abstracts', reviewing.RHListOtherAbstracts, methods=('POST',))

# Management dashboard
_bp.add_url_rule('/manage/abstracts/', 'management', management.RHAbstractsDashboard)

# CFA scheduling
_bp.add_url_rule('/manage/abstracts/schedule', 'schedule_abstracts_call', management.RHScheduleCFA,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/open', 'open_abstracts_call', management.RHOpenCFA, methods=('POST',))
_bp.add_url_rule('/manage/abstracts/close', 'close_abstracts_call', management.RHCloseCFA, methods=('POST',))

# Configuration
_bp.add_url_rule('/manage/abstracts/settings', 'manage_submission_settings', management.RHManageAbstractSubmission,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/review-settings', 'manage_reviewing_settings', management.RHManageAbstractReviewing,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/teams', 'manage_reviewing_roles', management.RHManageReviewingRoles,
                 methods=('GET', 'POST'))

# Abstract list (management)
_bp.add_url_rule('/manage/abstracts/list/', 'manage_abstract_list', abstract_list.RHAbstractList)
_bp.add_url_rule('/manage/abstracts/list/customize', 'customize_abstract_list', abstract_list.RHAbstractListCustomize,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/list/static-url', 'generate_static_url', abstract_list.RHAbstractListStaticURL,
                 methods=('POST',))
_bp.add_url_rule('/manage/abstracts/abstracts.pdf', 'abstracts_pdf_export', abstract_list.RHAbstractsExportPDF,
                 methods=('POST',))
_bp.add_url_rule('/manage/abstracts/abstracts.csv', 'abstracts_csv_export', abstract_list.RHAbstractsExportCSV,
                 methods=('POST',))
_bp.add_url_rule('/manage/abstracts/abstracts.xlsx', 'abstracts_xlsx_export', abstract_list.RHAbstractsExportExcel,
                 methods=('POST',))
_bp.add_url_rule('/manage/abstracts/abstracts.json', 'abstracts_json_export', abstract_list.RHAbstractsExportJSON,
                 methods=('POST',))
_bp.add_url_rule('/manage/abstracts/create', 'manage_create_abstract', abstract_list.RHCreateAbstract,
                 methods=('GET', 'POST'))

# Bulk abstract actions (management)
_bp.add_url_rule('/manage/abstracts/delete', 'manage_delete_abstracts', abstract_list.RHDeleteAbstracts,
                 methods=('POST',))
_bp.add_url_rule('/manage/abstracts/person-list', 'person_list', abstract_list.RHAbstractPersonList, methods=('POST',))
_bp.add_url_rule('/manage/abstracts/attachments', 'download_attachments', abstract_list.RHAbstractsDownloadAttachments,
                 methods=('POST',))
_bp.add_url_rule('/manage/abstracts/judge', 'manage_judge_abstracts', abstract_list.RHBulkAbstractJudgment,
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


# URLs available in both management and display areas
# Note: When adding a new one here make sure to specify `defaults=defaults`
#       for each rule. Otherwise you may not get the correct one.
for prefix, is_management in (('/manage/abstracts', True), ('/abstracts', False)):
    defaults = {'management': is_management}
    # Abstract display
    _bp.add_url_rule(prefix + '/<int:abstract_id>/', 'display_abstract', abstract.RHDisplayAbstract, defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/attachments/<file_id>/<filename>', 'download_attachment',
                     abstract.RHAbstractsDownloadAttachment, defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/abstract-reviews.pdf', 'manage_abstract_pdf_export',
                     abstract.RHAbstractExportFullPDF, defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/abstract.pdf', 'display_abstract_pdf_export',
                     abstract.RHAbstractExportPDF, defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/notifications', 'notification_log',
                     abstract.RHAbstractNotificationLog, defaults=defaults)
    # Abstract actions
    _bp.add_url_rule(prefix + '/<int:abstract_id>/edit', 'edit_abstract',
                     abstract.RHEditAbstract, methods=('GET', 'POST'), defaults=defaults)
    # Reviewing/judgment actions
    _bp.add_url_rule(prefix + '/<int:abstract_id>/withdraw', 'withdraw_abstract',
                     reviewing.RHWithdrawAbstract, methods=('POST',), defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/reset', 'reset_abstract_state',
                     reviewing.RHResetAbstractState, methods=('POST',), defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/judge', 'judge_abstract',
                     reviewing.RHJudgeAbstract, methods=('POST',), defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/reviewing-tracks', 'edit_review_tracks',
                     reviewing.RHEditReviewedForTrackList, methods=('GET', 'POST'), defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/review/track/<int:track_id>', 'review_abstract',
                     reviewing.RHSubmitAbstractReview, methods=('GET', 'POST'), defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/reviews/<int:review_id>/edit', 'edit_review',
                     reviewing.RHEditAbstractReview, methods=('GET', 'POST'), defaults=defaults)
    # Abstract comments
    _bp.add_url_rule(prefix + '/<int:abstract_id>/comment', 'comment_abstract',
                     reviewing.RHSubmitAbstractComment, methods=('POST',), defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/comments/<int:comment_id>', 'edit_abstract_comment',
                     reviewing.RHEditAbstractComment, methods=('GET', 'POST'), defaults=defaults)
    _bp.add_url_rule(prefix + '/<int:abstract_id>/comments/<int:comment_id>', 'delete_abstract_comment',
                     reviewing.RHDeleteAbstractComment, methods=('DELETE',), defaults=defaults)


@_bp.url_defaults
def _add_management_flag(endpoint, values):
    if ('management' not in values and
            endpoint.split('.')[0] == _bp.name and
            current_app.url_map.is_endpoint_expecting(endpoint, 'management')):
        values['management'] = g.rh.management


# Legacy URLs - display
_compat_bp = IndicoBlueprint('compat_abstracts', __name__, url_prefix='/event/<int:confId>')
_compat_bp.add_url_rule('/call-for-abstracts/', 'cfa', make_compat_redirect_func(_bp, 'call_for_abstracts'))
_compat_bp.add_url_rule('/call-for-abstracts/my-abstracts', 'mine',
                        make_compat_redirect_func(_bp, 'call_for_abstracts'))
_compat_bp.add_url_rule('/call-for-abstracts/my-abstracts.pdf', 'mine_pdf',
                        make_compat_redirect_func(_bp, 'my_abstracts_pdf'))
_compat_bp.add_url_rule('/call-for-abstracts/submit', 'submit', make_compat_redirect_func(_bp, 'call_for_abstracts'))
_compat_bp.add_url_rule('/call-for-abstracts/<int:friendly_id>/', 'abstract',
                        partial(compat_abstract, 'display_abstract'))
_compat_bp.add_url_rule('/call-for-abstracts/<int:friendly_id>/Abstract.pdf', 'abstract_pdf',
                        partial(compat_abstract, 'display_abstract_pdf_export'))
_compat_bp.add_url_rule('/abstract-book.pdf', 'boa', make_compat_redirect_func(_bp, 'export_boa'))

# Legacy URLs - management
_compat_bp.add_url_rule('/manage/call-for-abstracts/abstracts/', 'manage_cfa',
                        make_compat_redirect_func(_bp, 'manage_abstract_list'))
_compat_bp.add_url_rule('/manage/call-for-abstracts/abstracts/<int:friendly_id>/', 'manage_abstract',
                        partial(compat_abstract, 'display_abstract', management=True))
_compat_bp.add_url_rule('/manage/call-for-abstracts/abstracts/<int:friendly_id>/abstract.pdf',
                        'manage_abstract_pdf_export', partial(compat_abstract, 'manage_abstract_pdf_export',
                                                              management=True))

# Legacy URLs - reviewing
_compat_bp.add_url_rule('/manage/program/tracks/<int:track_id>/abstracts/',
                        'track_abstracts', make_compat_redirect_func(_bp, 'display_reviewable_tracks',
                                                                     view_args_conv={'track_id': None}))
_compat_bp.add_url_rule('/manage/program/tracks/<int:track_id>/abstracts/<int:friendly_id>/', 'track_abstract',
                        partial(compat_abstract, 'display_abstract'))
_compat_bp.add_url_rule('/manage/program/tracks/<int:track_id>/abstracts/<int:friendly_id>/abstract.pdf',
                        'track_abstract_pdf', partial(compat_abstract, 'display_abstract_pdf_export'))

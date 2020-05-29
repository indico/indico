# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.editing.controllers import frontend
from indico.modules.events.editing.controllers.backend import common, editable_list, management, service, timeline
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('event_editing', __name__, url_prefix='/event/<confId>', template_folder='templates',
                      virtual_template_folder='events/editing')

# Frontend (management)
_bp.add_url_rule('/manage/editing/', 'dashboard', frontend.RHEditingDashboard)
_bp.add_url_rule('/manage/editing/tags', 'manage_tags', frontend.RHEditingDashboard)
_bp.add_url_rule('/manage/editing/<any(paper,slides,poster):type>/', 'manage_editable_type',
                 frontend.RHEditingDashboard)
_bp.add_url_rule('/manage/editing/<any(paper,slides,poster):type>/list', 'manage_editable_type_list',
                 frontend.RHEditingDashboard)
_bp.add_url_rule('/manage/editing/<any(paper,slides,poster):type>/types', 'manage_file_types',
                 frontend.RHEditingDashboard)
_bp.add_url_rule('/manage/editing/<any(paper,slides,poster):type>/review-conditions', 'manage_review_conditions',
                 frontend.RHEditingDashboard)

# Frontend (timeline)
contrib_prefix = '/contributions/<int:contrib_id>/editing/<any(paper,slides,poster):type>'
_bp.add_url_rule(contrib_prefix, 'editable', frontend.RHEditableTimeline)
_bp.add_url_rule(contrib_prefix + '/<int:revision_id>/files.zip', 'revision_files_export',
                 timeline.RHExportRevisionFiles)
_bp.add_url_rule(contrib_prefix + '/<int:revision_id>/<int:file_id>/<filename>', 'download_file',
                 timeline.RHDownloadRevisionFile)

# Event-level APIs
review_cond_prefix = '/editing/api/<any(paper,slides,poster):type>/review-conditions'
_bp.add_url_rule(review_cond_prefix, 'api_review_conditions',
                 management.RHEditingReviewConditions, methods=('GET', 'POST'))
_bp.add_url_rule(review_cond_prefix + '/<int:condition_id>', 'api_edit_review_condition',
                 management.RHEditingEditReviewCondition, methods=('DELETE', 'PATCH'))
_bp.add_url_rule('/editing/api/<any(paper,slides,poster):type>/file-types', 'api_file_types',
                 common.RHEditingFileTypes)
_bp.add_url_rule('/editing/api/<any(paper,slides,poster):type>/file-types', 'api_add_file_type',
                 management.RHCreateFileType, methods=('POST',))
_bp.add_url_rule('/editing/api/<any(paper,slides,poster):type>/file-types/<int:file_type_id>', 'api_edit_file_type',
                 management.RHEditFileType, methods=('PATCH', 'DELETE'))
_bp.add_url_rule('/editing/api/tags', 'api_tags', common.RHEditingTags)
_bp.add_url_rule('/editing/api/tags', 'api_create_tag', management.RHCreateTag, methods=('POST',))
_bp.add_url_rule('/editing/api/tag/<int:tag_id>', 'api_edit_tag', management.RHEditTag, methods=('PATCH', 'DELETE'))
_bp.add_url_rule('/editing/api/menu-entries', 'api_menu_entries', common.RHMenuEntries)
_bp.add_url_rule('/editing/api/enabled-editable-types', 'api_enabled_editable_types',
                 management.RHEnabledEditableTypes, methods=('GET', 'POST'))
_bp.add_url_rule('/editing/api/<any(paper,slides,poster):type>/editable-assignment/self-assign-enabled',
                 'api_self_assign_enabled', management.RHEditableSetSelfAssign, methods=('GET', 'PUT', 'DELETE'))
_bp.add_url_rule('/editing/api/<any(paper,slides,poster):type>/principals', 'api_editable_type_principals',
                 management.RHEditableTypePrincipals, methods=('GET', 'POST'))
_bp.add_url_rule('/editing/api/<any(paper,slides,poster):type>/submission-enabled',
                 'api_submission_enabled', management.RHEditableSetSubmission, methods=('GET', 'PUT', 'DELETE'))
_bp.add_url_rule('/editing/api/<any(paper,slides,poster):type>/editing-enabled',
                 'api_editing_enabled', management.RHEditableSetEditing, methods=('GET', 'PUT', 'DELETE'))
_bp.add_url_rule('/editing/api/service/check-url', 'api_check_service_url', service.RHCheckServiceURL)
_bp.add_url_rule('/editing/api/service/connect', 'api_service_connect', service.RHConnectService, methods=('POST',))
_bp.add_url_rule('/editing/api/service/disconnect', 'api_service_disconnect', service.RHDisconnectService,
                 methods=('POST',))
_bp.add_url_rule('/editing/api/service/status', 'api_service_status', service.RHServiceStatus)
_bp.add_url_rule('/editing/api/<any(paper,slides,poster):type>/editables/prepare-archive', 'prepare_editables_archive',
                 editable_list.RHPrepareEditablesArchive, methods=('POST',))
_bp.add_url_rule('/editing/<any(paper,slides,poster):type>/editables/archive/<uuid:uuid>.zip', 'download_archive',
                 editable_list.RHDownloadArchive)
_bp.add_url_rule('/editing/api/<any(paper,slides,poster):type>/editables/assign', 'assign_editor',
                 editable_list.RHAssignEditor, methods=('POST',))
_bp.add_url_rule('/editing/api/<any(paper,slides,poster):type>/editables/assign/me', 'assign_myself',
                 editable_list.RHAssignMyselfAsEditor, methods=('POST',))
_bp.add_url_rule('/editing/api/<any(paper,slides,poster):type>/editables/unassign', 'unassign_editor',
                 editable_list.RHUnassignEditor, methods=('POST',))

# Editable-level APIs
contrib_api_prefix = '/api' + contrib_prefix
_bp.add_url_rule(contrib_api_prefix + '/editor/', 'api_unassign_editable', timeline.RHEditableUnassign,
                 methods=('DELETE',))
_bp.add_url_rule(contrib_api_prefix + '/editor/me', 'api_assign_editable_self', timeline.RHEditableAssignMe,
                 methods=('PUT',))

# Contribution/revision-level APIs
_bp.add_url_rule(contrib_api_prefix, 'api_editable', timeline.RHEditable)
_bp.add_url_rule(contrib_api_prefix, 'api_create_editable', timeline.RHCreateEditable, methods=('PUT',))
_bp.add_url_rule(contrib_api_prefix + '/upload', 'api_upload', timeline.RHEditingUploadFile, methods=('POST',))
_bp.add_url_rule(contrib_api_prefix + '/<int:revision_id>/review', 'api_review_editable',
                 timeline.RHReviewEditable, methods=('POST',))
_bp.add_url_rule(contrib_api_prefix + '/<int:revision_id>/confirm', 'api_confirm_changes',
                 timeline.RHConfirmEditableChanges, methods=('POST',),)
_bp.add_url_rule(contrib_api_prefix + '/<int:revision_id>/replace', 'api_replace_revision',
                 timeline.RHReplaceRevision, methods=('POST',))
_bp.add_url_rule(contrib_api_prefix + '/<int:revision_id>/new', 'api_create_submitter_revision',
                 timeline.RHCreateSubmitterRevision, methods=('POST',),)
_bp.add_url_rule(contrib_api_prefix + '/<int:revision_id>/review', 'api_undo_review',
                 timeline.RHUndoReview, methods=('DELETE',))
_bp.add_url_rule(contrib_api_prefix + '/<int:revision_id>/comments/', 'api_create_comment',
                 timeline.RHCreateRevisionComment, methods=('POST',),)
_bp.add_url_rule(contrib_api_prefix + '/<int:revision_id>/comments/<int:comment_id>',
                 'api_edit_comment', timeline.RHEditRevisionComment, methods=('PATCH', 'DELETE'),)

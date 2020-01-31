# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.editing.controllers import frontend
from indico.modules.events.editing.controllers.backend import common, management, timeline
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('event_editing', __name__, url_prefix='/event/<confId>', template_folder='templates',
                      virtual_template_folder='events/editing')

# Frontend
_bp.add_url_rule('/manage/editing/', 'dashboard', frontend.RHEditingDashboard)
_bp.add_url_rule('/manage/editing/tags', 'manage_tags', frontend.RHManageEditingTags)
_bp.add_url_rule('/manage/editing/types', 'manage_file_types', frontend.RHManageEditingFileTypes)
_bp.add_url_rule('/manage/editing/review-conditions', 'manage_review_conditions',
                 frontend.RHManageEditingReviewConditions)
_bp.add_url_rule('/contributions/<int:contrib_id>/editing/<any(paper):type>', 'editable', frontend.RHEditableTimeline)
_bp.add_url_rule('/contributions/<int:contrib_id>/editing/<any(paper):type>/<int:revision_id>/files.zip',
                 'revision_files_export', timeline.RHExportRevisionFiles)
_bp.add_url_rule('/contributions/<int:contrib_id>/editing/<any(paper):type>/<int:revision_id>/<int:file_id>/<filename>',
                 'download_file', timeline.RHDownloadRevisionFile)

# Event-level APIs
_bp.add_url_rule('/editing/api/review-conditions', 'api_review_conditions', management.RHEditingReviewConditions,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/editing/api/review-conditions/<uuid:uuid>', 'api_edit_review_condition',
                 management.RHEditingEditReviewCondition, methods=('DELETE', 'PATCH'))
_bp.add_url_rule('/editing/api/file-types', 'api_file_types', common.RHEditingFileTypes)
_bp.add_url_rule('/editing/api/file-types', 'api_add_file_type', management.RHCreateFileType, methods=('POST',))
_bp.add_url_rule('/editing/api/file-types/<int:file_type_id>', 'api_edit_file_type', management.RHEditFileType,
                 methods=('PATCH', 'DELETE'))
_bp.add_url_rule('/editing/api/tags', 'api_tags', common.RHEditingTags)
_bp.add_url_rule('/editing/api/tags', 'api_create_tag', management.RHCreateTag, methods=('POST',))
_bp.add_url_rule('/editing/api/tag/<int:tag_id>', 'api_edit_tag', management.RHEditTag, methods=('PATCH', 'DELETE'))

# Contribution/revision-level APIs
_bp.add_url_rule('/api/contributions/<int:contrib_id>/editing/<any(paper):type>/upload', 'api_upload',
                 timeline.RHEditingUploadFile, methods=('POST',))
_bp.add_url_rule('/api/contributions/<int:contrib_id>/editing/<any(paper):type>',
                 'api_editable', timeline.RHEditable)
_bp.add_url_rule('/api/contributions/<int:contrib_id>/editing/<any(paper):type>',
                 'api_create_editable', timeline.RHCreateEditable, methods=('PUT',))
_bp.add_url_rule('/api/contributions/<int:contrib_id>/editing/<any(paper):type>/<int:revision_id>/review',
                 'api_review_editable', timeline.RHReviewEditable, methods=('POST',))
_bp.add_url_rule('/api/contributions/<int:contrib_id>/editing/<any(paper):type>/<int:revision_id>/confirm',
                 'api_confirm_changes', timeline.RHConfirmEditableChanges, methods=('POST',))
_bp.add_url_rule('/api/contributions/<int:contrib_id>/editing/<any(paper):type>/<int:revision_id>/replace',
                 'api_replace_revision', timeline.RHReplaceRevision, methods=('POST',))
_bp.add_url_rule('/api/contributions/<int:contrib_id>/editing/<any(paper):type>/<int:revision_id>/new',
                 'api_create_submitter_revision', timeline.RHCreateSubmitterRevision, methods=('POST',))
_bp.add_url_rule('/api/contributions/<int:contrib_id>/editing/<any(paper):type>/<int:revision_id>/review',
                 'api_undo_review', timeline.RHUndoReview, methods=('DELETE',))
_bp.add_url_rule('/api/contributions/<int:contrib_id>/editing/<any(paper):type>/<int:revision_id>/comments/',
                 'api_create_comment', timeline.RHCreateRevisionComment, methods=('POST',))
_bp.add_url_rule(
    '/api/contributions/<int:contrib_id>/editing/<any(paper):type>/<int:revision_id>/comments/<int:comment_id>',
    'api_edit_comment', timeline.RHEditRevisionComment, methods=('PATCH', 'DELETE')
)

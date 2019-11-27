# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.editing.controllers import backend, frontend
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('event_editing', __name__, url_prefix='/event/<confId>', template_folder='templates',
                      virtual_template_folder='events/editing')

# Frontend
_bp.add_url_rule('/contributions/<int:contrib_id>/editing/<any(paper):type>', 'editable', frontend.RHEditableTimeline)

# Event-level APIs
_bp.add_url_rule('/editing/api/file-types', 'api_file_types', backend.RHEditingFileTypes)
_bp.add_url_rule('/editing/api/tags', 'api_tags', backend.RHEditingTags)

# Contribution/revision-level APIs
_bp.add_url_rule('/contributions/<int:contrib_id>/editing/<any(paper):type>/<int:revision_id>/files.zip',
                 'revision_files_export', backend.RHExportRevisionFiles)
_bp.add_url_rule('/contributions/<int:contrib_id>/editing/<any(paper):type>/<int:revision_id>/<int:file_id>/<filename>',
                 'download_file', backend.RHDownloadRevisionFile)
_bp.add_url_rule('/api/contributions/<int:contrib_id>/editing/<any(paper):type>/upload', 'api_upload',
                 backend.RHEditingUploadFile, methods=('POST',))
_bp.add_url_rule('/api/contributions/<int:contrib_id>/editing/<any(paper):type>',
                 'api_editable', backend.RHEditable)
_bp.add_url_rule('/api/contributions/<int:contrib_id>/editing/<any(paper):type>',
                 'api_create_editable', backend.RHCreateEditable, methods=('PUT',))
_bp.add_url_rule('/api/contributions/<int:contrib_id>/editing/<any(paper):type>/<int:revision_id>/review',
                 'api_review_editable', backend.RHReviewEditable, methods=('POST',))
_bp.add_url_rule('/api/contributions/<int:contrib_id>/editing/<any(paper):type>/<int:revision_id>/confirm',
                 'api_confirm_changes', backend.RHConfirmEditableChanges, methods=('POST',))
_bp.add_url_rule('/api/contributions/<int:contrib_id>/editing/<any(paper):type>/<int:revision_id>/replace',
                 'api_replace_revision', backend.RHReplaceRevision, methods=('POST',))
_bp.add_url_rule('/api/contributions/<int:contrib_id>/editing/<any(paper):type>/<int:revision_id>/new',
                 'api_create_submitter_revision', backend.RHCreateSubmitterRevision, methods=('POST',))
_bp.add_url_rule('/api/contributions/<int:contrib_id>/editing/<any(paper):type>/<int:revision_id>/review',
                 'api_undo_review', backend.RHUndoReview, methods=('DELETE',))
_bp.add_url_rule('/api/contributions/<int:contrib_id>/editing/<any(paper):type>/<int:revision_id>/comments/',
                 'api_create_comment', backend.RHCreateRevisionComment, methods=('POST',))
_bp.add_url_rule(
    '/api/contributions/<int:contrib_id>/editing/<any(paper):type>/<int:revision_id>/comments/<int:comment_id>',
    'api_edit_comment', backend.RHEditRevisionComment, methods=('PATCH', 'DELETE')
)

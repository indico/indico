# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from markupsafe import escape
from marshmallow import ValidationError, fields, post_dump, validates_schema
from marshmallow_enum import EnumField

from indico.core.marshmallow import mm
from indico.modules.events.contributions.schemas import ContributionSchema
from indico.modules.events.editing.models.comments import EditingRevisionComment
from indico.modules.events.editing.models.editable import Editable
from indico.modules.events.editing.models.file_types import EditingFileType
from indico.modules.events.editing.models.revision_files import EditingRevisionFile
from indico.modules.events.editing.models.revisions import EditingRevision
from indico.modules.events.editing.models.tags import EditingTag
from indico.modules.users.schemas import UserSchema
from indico.util.struct.enum import IndicoEnum


class RevisionState(mm.Schema):
    title = fields.String()
    name = fields.String()
    css_class = fields.String()


class EditingFileTypeSchema(mm.ModelSchema):
    class Meta:
        model = EditingFileType
        fields = ('id', 'name', 'extensions', 'allow_multiple_files', 'required', 'publishable')


class EditingTagSchema(mm.ModelSchema):
    class Meta:
        model = EditingTag
        fields = ('id', 'name', 'color', 'system')

    @post_dump(pass_many=True)
    def convert_to_dict(self, data, many, **kwargs):
        if many:
            data = {x['id']: x for x in data}
        return data


class EditingRevisionFileSchema(mm.ModelSchema):
    class Meta:
        model = EditingRevisionFile
        fields = ('uuid', 'filename', 'size', 'content_type', 'file_type', 'download_url')

    uuid = fields.String(attribute='file.uuid')
    filename = fields.String(attribute='file.filename')
    size = fields.Int(attribute='file.size')
    content_type = fields.String(attribute='file.content_type')
    download_url = fields.String()


class EditingRevisionCommentSchema(mm.ModelSchema):
    class Meta:
        model = EditingRevisionComment
        fields = ('id', 'user', 'created_dt', 'modified_dt', 'internal', 'system', 'text', 'html')

    user = fields.Nested(UserSchema, only=('id', 'avatar_bg_color', 'full_name'))
    html = fields.Function(lambda comment: escape(comment.text))
    # TODO: filter out internal comments depending on who's viewing


class EditingRevisionSchema(mm.ModelSchema):
    class Meta:
        model = EditingRevision
        fields = ('id', 'created_dt', 'submitter', 'editor', 'files', 'comment', 'comment_html', 'comments',
                  'initial_state', 'final_state', 'tags')

    comment_html = fields.Function(lambda rev: escape(rev.comment))
    submitter = fields.Nested(UserSchema, only=('id', 'avatar_bg_color', 'full_name'))
    editor = fields.Nested(UserSchema, only=('id', 'avatar_bg_color', 'full_name'))
    files = fields.List(fields.Nested(EditingRevisionFileSchema))
    comments = fields.List(fields.Nested(EditingRevisionCommentSchema))
    initial_state = fields.Nested(RevisionState)
    final_state = fields.Nested(RevisionState)


class EditableSchema(mm.ModelSchema):
    class Meta:
        model = Editable
        fields = ('id', 'type', 'editor', 'revisions', 'contribution')

    contribution = fields.Nested(ContributionSchema)
    editor = fields.Nested(UserSchema, only=('id', 'avatar_bg_color', 'full_name'))
    revisions = fields.List(fields.Nested(EditingRevisionSchema))


class EditingReviewAction(IndicoEnum):
    accept = 'accept'
    reject = 'reject'
    update = 'update'
    request_update = 'request_update'


class ReviewEditableArgs(mm.Schema):
    action = EnumField(EditingReviewAction, required=True)
    comment = fields.String(missing='')

    @validates_schema(skip_on_field_errors=True)
    def validate_everything(self, data):
        if data['action'] != EditingReviewAction.accept and not data['comment']:
            raise ValidationError('This field is required', 'comment')


class EditingConfirmationAction(IndicoEnum):
    accept = 'accept'
    reject = 'reject'

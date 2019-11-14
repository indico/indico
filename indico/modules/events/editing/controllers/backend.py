# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import request, session
from werkzeug.exceptions import Forbidden, NotFound

from indico.core.errors import UserValueError
from indico.modules.events.contributions.controllers.display import RHContributionDisplayBase
from indico.modules.events.controllers.base import RHEventBase
from indico.modules.events.editing.fields import EditingFilesField, EditingTagsField
from indico.modules.events.editing.models.editable import Editable, EditableType
from indico.modules.events.editing.operations import create_new_editable, review_editable_revision
from indico.modules.events.editing.schemas import (EditableSchema, EditingFileTypeSchema, EditingReviewAction,
                                                   EditingTagSchema, ReviewEditableArgs)
from indico.util.i18n import _
from indico.web.args import parser, use_kwargs


class RHEditingFileTypes(RHEventBase):
    def _process(self):
        return EditingFileTypeSchema(many=True).jsonify(self.event.editing_file_types)


class RHEditingTags(RHEventBase):
    def _process(self):
        return EditingTagSchema(many=True).jsonify(self.event.editing_tags)


class RHContributionEditableBase(RHContributionDisplayBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.contrib
        },
        'preserved_args': {'type'}
    }

    def _process_args(self):
        RHContributionDisplayBase._process_args(self)
        self.editable = (Editable.query
                         .with_parent(self.contrib)
                         .filter_by(type=EditableType[request.view_args['type']])
                         .first())

    def _check_access(self):
        RHContributionDisplayBase._check_access(self)
        # TODO: check if the user is authorized to submit an editable
        if not session.user:
            raise Forbidden


class RHContributionEditableRevisionBase(RHContributionEditableBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.contrib
        },
        'preserved_args': {'type', 'revision_id'}
    }

    def _process_args(self):
        RHContributionEditableBase._process_args(self)
        if not self.editable:
            raise NotFound
        self.revision = self.editable.revisions[-1]
        if self.revision.id != request.view_args['revision_id']:
            raise UserValueError(_('Only the latest revision can be reviewed'))

    def _check_access(self):
        RHContributionEditableBase._check_access(self)
        # TODO: check if the user has the correct permissions on the editable revision


class RHEditable(RHContributionEditableBase):
    def _process(self):
        return EditableSchema().jsonify(self.editable)


class RHCreateEditable(RHContributionEditableBase):
    def _process(self):
        if self.editable:
            raise UserValueError('Editable already exists')

        args = parser.parse({
            'files': EditingFilesField(self.event, required=True)
        })

        create_new_editable(self.contrib, EditableType[request.view_args['type']], session.user, args['files'])
        return '', 201


class RHReviewEditable(RHContributionEditableRevisionBase):
    @use_kwargs(ReviewEditableArgs())
    def _process(self, action, comment):
        argmap = {'tags': EditingTagsField(self.event, missing=set())}
        if action == EditingReviewAction.update:
            argmap['files'] = EditingFilesField(self.event, allow_claimed_files=True, required=True)
        args = parser.parse(argmap)
        review_editable_revision(self.revision, session.user, action, comment, args['tags'], args.get('files'))
        return '', 204

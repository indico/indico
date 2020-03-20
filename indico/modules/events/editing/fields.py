# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import fnmatch
import os

from marshmallow import ValidationError
from marshmallow.fields import Dict

from indico.modules.events.editing.models.file_types import EditingFileType
from indico.modules.events.editing.models.tags import EditingTag
from indico.util.marshmallow import FilesField, ModelField, ModelList


class EditingFilesField(Dict):
    def __init__(self, event, contrib, allow_claimed_files=False, **kwargs):
        self.event = event
        self.contrib = contrib
        keys_field = ModelField(EditingFileType, get_query=lambda m: m.query.with_parent(event))
        values_field = FilesField(required=True, allow_claimed=allow_claimed_files)
        validators = kwargs.pop('validate', []) + [self.validate_files]
        super(EditingFilesField, self).__init__(keys=keys_field, values=values_field, validate=validators, **kwargs)

    def validate_files(self, value):
        required_types = {ft for ft in self.event.editing_file_types if ft.required}

        # ensure all required file types have files
        required_missing = required_types - {ft for ft, files in value.viewitems() if files}
        if required_missing:
            raise ValidationError('Required file types missing: {}'
                                  .format(', '.join(ft.name for ft in required_missing)))

        seen = set()
        for file_type, files in value.viewitems():
            # ensure single-file types don't have too many files
            if not file_type.allow_multiple_files and len(files) > 1:
                raise ValidationError('File type "{}" allows only one file'.format(file_type.name))

            # ensure all files have allowed extensions
            valid_extensions = {ext.lower() for ext in file_type.extensions}
            if valid_extensions:
                extensions = {os.path.splitext(f.filename)[1].lstrip('.').lower() for f in files}
                invalid_extensions = extensions - valid_extensions
                if invalid_extensions:
                    raise ValidationError('File type "{}" does not allow these extensions: {}'
                                          .format(file_type.name, ', '.join(invalid_extensions)))

            # ensure all filenames conform to the template
            if file_type.filename_template:
                filenames = {os.path.splitext(f.filename)[0] for f in files}
                filename_template = file_type.filename_template.replace('{code}', self.contrib.code)
                if not all(fnmatch.fnmatch(filename, filename_template) for filename in filenames):
                    raise ValidationError("Some files don't conform to the filename template '{}'"
                                          .format(file_type.filename_template))

            # ensure each file is only used in one type
            duplicates = set(files) & seen
            if duplicates:
                raise ValidationError('Files found in multiple types: {}'
                                      .format(', '.join(unicode(f.uuid) for f in duplicates)))

            seen |= set(files)


class EditingTagsField(ModelList):
    def __init__(self, event, allow_system_tags=False, **kwargs):
        def _get_query(m):
            query = m.query.with_parent(event)
            if not allow_system_tags:
                query = query.filter_by(system=False)
            return query

        super(EditingTagsField, self).__init__(model=EditingTag, get_query=_get_query, collection_class=set, **kwargs)

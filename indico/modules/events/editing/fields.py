# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import fnmatch
import os

from marshmallow import ValidationError
from marshmallow.fields import Dict

from indico.modules.events.contributions import Contribution
from indico.modules.events.editing.models.editable import Editable
from indico.modules.events.editing.models.file_types import EditingFileType
from indico.modules.events.editing.models.tags import EditingTag
from indico.util.marshmallow import FilesField, ModelField, ModelList


class EditingFilesField(Dict):
    def __init__(self, event=None, contrib=None, editable_type=None, /, *, allow_claimed_files=False, **kwargs):
        self.event = event
        self.contrib = contrib
        self.editable_type = editable_type

        def _get_query(m, ctx):
            return self._get_editing_file_types_query(event or ctx['event'], editable_type or ctx['editable_type'])

        keys_field = ModelField(EditingFileType, get_query=_get_query)
        values_field = FilesField(required=True, allow_claimed=allow_claimed_files)
        super().__init__(keys=keys_field, values=values_field, **kwargs)

    def _get_editing_file_types_query(self, event, editable_type):
        return EditingFileType.query.with_parent(event).filter_by(type=editable_type)

    def _deserialize(self, value, attr, data, **kwargs):
        rv = super()._deserialize(value, attr, data, **kwargs)
        self.validate_files(rv)
        return rv

    def validate_files(self, value):
        contrib = self.contrib or self.context['contrib']

        required_types = {
            ft
            for ft in self._get_editing_file_types_query(
                self.event or self.context['event'], self.editable_type or self.context['editable_type']
            )
            if ft.required
        }

        # ensure all required file types have files
        required_missing = required_types - {ft for ft, files in value.items() if files}
        if required_missing:
            raise ValidationError('Required file types missing: {}'
                                  .format(', '.join(ft.name for ft in required_missing)))

        seen = set()
        for file_type, files in value.items():
            # ensure single-file types don't have too many files
            if not file_type.allow_multiple_files and len(files) > 1:
                raise ValidationError(f'File type "{file_type.name}" allows only one file')

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
                filename_template = file_type.filename_template.replace('{code}', contrib.code)
                if not all(fnmatch.fnmatch(filename, filename_template) for filename in filenames):
                    raise ValidationError(
                        f"Some files do not conform to the filename template '{file_type.filename_template}'"
                    )

            # ensure each file is only used in one type
            duplicates = set(files) & seen
            if duplicates:
                raise ValidationError('Files found in multiple types: {}'
                                      .format(', '.join(str(f.uuid) for f in duplicates)))

            # ensure no duplicate filenames
            if len({f.filename for f in files}) != len(files):
                raise ValidationError(f'Duplicate filenames found in file type "{file_type.name}"')

            seen |= set(files)


class EditingTagsField(ModelList):
    def __init__(self, event=None, /, *, allow_system_tags=None, **kwargs):
        def _get_query(m, ctx):
            query = m.query.with_parent(event or ctx['event'])
            if not allow_system_tags:
                query = query.filter_by(system=False)
            return query

        super().__init__(model=EditingTag, get_query=_get_query, collection_class=set, **kwargs)


class EditableList(ModelList):
    def __init__(self, event, editable_type, /, **kwargs):
        def _get_query(m, ctx):
            return (m.query
                    .join(Contribution)
                    .filter(~Contribution.is_deleted, Contribution.event_id == event.id, m.type == editable_type))
        super().__init__(model=Editable, get_query=_get_query, collection_class=set, **kwargs)

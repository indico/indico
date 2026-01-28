# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import fnmatch
import json
import os

from marshmallow import ValidationError
from marshmallow.fields import Dict

from indico.modules.events.papers.file_types import PaperFileType
from indico.modules.events.papers.settings import RoleConverter
from indico.modules.events.papers.settings import paper_reviewing_settings as settings
from indico.util.marshmallow import FilesField, ModelField
from indico.web.forms.fields import JSONField
from indico.web.forms.widgets import JinjaWidget


class PaperEmailSettingsField(JSONField):
    CAN_POPULATE = True
    widget = JinjaWidget('events/papers/forms/paper_email_settings_widget.html')

    @property
    def event(self):
        return self.get_form().event

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = json.loads(valuelist[0])
            data = {}
            for key, value in self.data.items():
                data[key] = RoleConverter.to_python(value) if isinstance(value, list) else value
            self.data = data

    def _value(self):
        return {
            'notify_on_added_to_event': [x.name for x in settings.get(self.event, 'notify_on_added_to_event')],
            'notify_on_assigned_contrib': [x.name for x in settings.get(self.event, 'notify_on_assigned_contrib')],
            'notify_on_paper_submission': [x.name for x in settings.get(self.event, 'notify_on_paper_submission')],
            'notify_judge_on_review': settings.get(self.event, 'notify_judge_on_review'),
            'notify_author_on_judgment': settings.get(self.event, 'notify_author_on_judgment')
        }


class PaperFilesField(Dict):
    def __init__(self, event=None, contrib=None, **kwargs):
        self.event = event
        self.contrib = contrib

        def _get_query(m, ctx):
            return self._get_file_types_query(event or ctx['event'])

        keys_field = ModelField(PaperFileType, get_query=_get_query)
        values_field = FilesField(required=True)
        super().__init__(keys=keys_field, values=values_field, **kwargs)

    def _get_file_types_query(self, event):
        return PaperFileType.query.with_parent(event)

    def _deserialize(self, value, attr, data, **kwargs):
        rv = super()._deserialize(value, attr, data, **kwargs)
        self.validate_files(rv)
        return rv

    def validate_files(self, value):
        required_types = {ft for ft in self._get_file_types_query(self.event or self.context['event']) if ft.required}

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
                filename_template = file_type.filename_template.replace('{code}', self.contrib.code)
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

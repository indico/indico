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

from __future__ import absolute_import, unicode_literals

from flask import json
from werkzeug.datastructures import FileStorage
from wtforms import Field

from indico.core.config import config
from indico.web.flask.templating import get_template_module
from indico.web.forms.widgets import JinjaWidget


class FileField(Field):
    """A dropzone field"""

    widget = JinjaWidget('forms/dropzone_widget.html', editable=False)

    default_options = {
        'multiple_files': False,
        'max_files': 10,
        'add_remove_links': True,
        'handle_flashes': False,
        'lightweight': False
    }

    def __init__(self, *args, **kwargs):
        self.lightweight = kwargs.pop('lightweight', self.default_options['lightweight'])

        max_file_size = kwargs.pop('max_file_size', None)
        if max_file_size is None:
            max_file_size = min(config.MAX_UPLOAD_FILE_SIZE or 10240,
                                config.MAX_UPLOAD_FILES_TOTAL_SIZE or 10240)  # in MB
        self.allow_multiple_files = kwargs.pop('multiple_files', self.default_options['multiple_files'])
        self.widget_options = {
            'url': kwargs.pop('post_url', None),
            'uploadMultiple': self.allow_multiple_files,
            'maxFilesize': max_file_size,
            'maxFiles': kwargs.pop('max_files', self.default_options['max_files']) if self.allow_multiple_files else 1,
            'addRemoveLinks': kwargs.pop('add_remove_links', self.default_options['add_remove_links']),
            'acceptedFiles': kwargs.pop('accepted_file_types', None),
            'parallelUploads': kwargs.pop('max_files', self.default_options['max_files']),
            'handleFlashes': kwargs.pop('handle_flashes', self.default_options['handle_flashes'])
        }

        if self.lightweight:
            tpl = get_template_module('forms/_dropzone_themes.html')
            self.widget_options['previewTemplate'] = tpl.thin_preview_template()
            self.widget_options['dictRemoveFile'] = tpl.remove_icon()

        super(FileField, self).__init__(*args, **kwargs)
        self.widget_options['paramName'] = self.name

    def process_formdata(self, valuelist):
        self.data = None
        if self.allow_multiple_files:
            self.data = valuelist
        elif valuelist:
            self.data = valuelist[0]

    def _value(self):
        return None


def get_file_metadata(file_):
    return {'id': file_.id, 'filename': file_.filename, 'content_type': file_.content_type, 'size': file_.size}


class EditableFileField(FileField):
    """A dropzone field that displays its current state and keeps track of deletes."""

    widget = JinjaWidget('forms/dropzone_widget.html', editable=True)

    def __init__(self, *args, **kwargs):
        self.get_metadata = kwargs.pop('get_metadata', get_file_metadata)
        self.added_only = kwargs.pop('added_only', False)
        super(EditableFileField, self).__init__(*args, **kwargs)
        self.widget_options['editable'] = True

    def process_formdata(self, valuelist):
        uploaded = []
        deleted = []

        for value in valuelist:
            if isinstance(value, FileStorage):
                uploaded.append(value)
            else:
                deleted = json.loads(value)
        if not self.allow_multiple_files:
            uploaded = uploaded[0] if uploaded else None
            deleted = deleted[0] if deleted else None
        self.data = uploaded if self.added_only else {
            'added': uploaded,
            'deleted': deleted
        }

    def _value(self):
        # If form validation fails we still have the dict from `process_formdata`
        # in `self.data` which cannot be serialized so we fallback to the default
        # data (if there is any, i.e. if we were editing something)
        # It would be cleaner to still take e.g. 'deleted' into account and
        # save/restore the selected files with JavaScript but in most cases our
        # client-side validation should not fail anyway...
        data = self.object_data if isinstance(self.data, dict) else self.data
        if self.allow_multiple_files:
            return [self.get_metadata(f) for f in data] if data else []
        else:
            return self.get_metadata(data) if data else None

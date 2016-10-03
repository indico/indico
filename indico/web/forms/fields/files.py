# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals, absolute_import

from wtforms import Field

from indico.core.config import Config
from indico.web.flask.templating import get_template_module
from indico.web.forms.widgets import JinjaWidget


class FileField(Field):
    """A dropzone field"""

    widget = JinjaWidget('forms/dropzone_widget.html')

    default_options = {
        'multiple_files': False,
        'max_files': 10,
        'add_remove_links': True,
        'param_name': 'file',
        'handle_flashes': False,
        'lightweight': False
    }

    def __init__(self, *args, **kwargs):
        self.get_metadata = kwargs.pop('get_metadata', None)
        self.lightweight = kwargs.pop('lightweight', self.default_options['lightweight'])

        config = Config.getInstance()
        max_file_size = kwargs.pop('max_file_size', None)
        if max_file_size is None:
            max_file_size = min(config.getMaxUploadFileSize() or 10240,
                                config.getMaxUploadFilesTotalSize() or 10240)  # in MB
        self.allow_multiple_files = kwargs.pop('multiple_files', self.default_options['multiple_files'])
        self.widget_options = {
            'url': kwargs.pop('post_url', None),
            'uploadMultiple': self.allow_multiple_files,
            'maxFilesize': max_file_size,
            'maxFiles': kwargs.pop('max_files', self.default_options['max_files']) if self.allow_multiple_files else 1,
            'addRemoveLinks': kwargs.pop('add_remove_links', self.default_options['add_remove_links']),
            'acceptedFiles': kwargs.pop('accepted_file_types', None),
            'paramName': kwargs.pop('param_name', self.default_options['param_name']),
            'parallelUploads': kwargs.pop('max_files', self.default_options['max_files']),
            'handleFlashes': kwargs.pop('handle_flashes', self.default_options['handle_flashes'])
        }

        if self.lightweight:
            tpl = get_template_module('forms/_dropzone_themes.html')
            self.widget_options['previewTemplate'] = tpl.thin_preview_template()
            self.widget_options['dictRemoveFile'] = tpl.remove_icon()

        super(FileField, self).__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        self.data = None
        if self.allow_multiple_files:
            self.data = valuelist
        elif valuelist:
            self.data = valuelist[0]

    def _value(self):
        return self.get_metadata(self) if self.get_metadata else None

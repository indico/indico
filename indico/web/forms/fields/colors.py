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

from indico.core.db.sqlalchemy.colors import ColorTuple
from indico.util.i18n import _
from indico.web.forms.fields import JSONField
from indico.web.forms.widgets import JinjaWidget


class IndicoPalettePickerField(JSONField):
    """Field allowing user to pick a color from a set of predefined values"""

    widget = JinjaWidget('forms/palette_picker_widget.html')
    CAN_POPULATE = True

    def __init__(self, *args, **kwargs):
        self.color_list = kwargs.pop('color_list')
        super(IndicoPalettePickerField, self).__init__(*args, **kwargs)

    def pre_validate(self, form):
        if self.data not in self.color_list:
            raise ValueError(_('Invalid colors selected'))

    def process_formdata(self, valuelist):
        super(IndicoPalettePickerField, self).process_formdata(valuelist)
        self.data = ColorTuple(self.data['text'], self.data['background'])

    def process_data(self, value):
        super(IndicoPalettePickerField, self).process_data(value)
        if self.object_data and self.object_data not in self.color_list:
            self.color_list = self.color_list + [self.object_data]

    def _value(self):
        return self.data._asdict()


class IndicoSinglePalettePickerField(IndicoPalettePickerField):
    """Like IndicoPalettePickerField but for just a single color."""

    def __init__(self, *args, **kwargs):
        self.text_color = kwargs.pop('text_color')
        kwargs['color_list'] = [ColorTuple(self.text_color, color) for color in kwargs['color_list']]
        super(IndicoSinglePalettePickerField, self).__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        super(IndicoSinglePalettePickerField, self).process_formdata(valuelist)
        self.data = self.data.background

    def pre_validate(self, form):
        if not any(self.data == color.background for color in self.color_list):
            raise ValueError(_('Invalid color selected'))

    def _value(self):
        return ColorTuple(self.text_color, self.data)._asdict()

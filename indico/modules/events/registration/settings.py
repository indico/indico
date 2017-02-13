# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals

from indico.core.settings.converters import EnumConverter
from indico.modules.designer import PageOrientation, PageSize
from indico.modules.events.registration.models.items import PersonalDataType
from indico.modules.events.settings import EventSettingsProxy


DEFAULT_BADGE_SETTINGS = {
    'top_margin': 1.6,
    'bottom_margin': 1.1,
    'left_margin': 1.6,
    'right_margin': 1.4,
    'margin_columns': 1.0,
    'margin_rows': 0.0,
    'page_size': PageSize.A4,
    'page_orientation': PageOrientation.portrait,
    'dashed_border': True
}

BADGE_SETTING_CONVERTERS = {
    'page_orientation': EnumConverter(PageOrientation),
    'page_size': EnumConverter(PageSize)
}


class RegistrationSettingsProxy(EventSettingsProxy):
    """Store per-event registration settings"""

    def get_participant_list_columns(self, event, form=None):
        if form is None:
            # Columns when forms are merged
            return self.get(event, 'participant_list_columns')
        else:
            try:
                # The int values are automatically converted to unicode when saved as JSON
                form_columns = self.get(event, 'participant_list_form_columns')[unicode(form.id)]
                return map(int, form_columns)
            except (ValueError, KeyError):
                # No settings for this form, default to the ones for the merged form
                column_names = self.get_participant_list_columns(event)
                return [form.get_personal_data_field_id(PersonalDataType[name]) for name in column_names]

    def set_participant_list_columns(self, event, columns, form=None):
        if form is None:
            if columns:
                self.set(event, 'participant_list_columns', columns)
            else:
                self.delete(event, 'participant_list_columns')
        else:
            form_columns = self.get(event, 'participant_list_form_columns')
            if columns:
                # The int values are automatically converted to unicode when saved
                # as JSON. Do it explicitely so that it keeps working if the
                # behavior changes and makes sense with the code above.
                form_columns[unicode(form.id)] = columns
            else:
                form_columns.pop(unicode(form.id), None)
            self.set(event, 'participant_list_form_columns', form_columns)

    def get_participant_list_form_ids(self, event):
        # Int values are converted to str when saved as JSON
        return map(int, self.get(event, 'participant_list_forms'))

    def set_participant_list_form_ids(self, event, form_ids):
        self.set(event, 'participant_list_forms', form_ids)


event_badge_settings = EventSettingsProxy('badge', DEFAULT_BADGE_SETTINGS, converters=BADGE_SETTING_CONVERTERS)

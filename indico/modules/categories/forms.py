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

from __future__ import unicode_literals

from wtforms.fields import SelectField, StringField
from wtforms.validators import DataRequired, ValidationError

from indico.util.i18n import _, ngettext
from indico.modules.categories.models.categories import EventMessageMode
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import (IndicoEnumSelectField, IndicoMarkdownField, IndicoThemeSelectField,
                                     IndicoTimezoneSelectField, EmailListField, JSONField)
from indico.web.forms.widgets import DropzoneWidget


def calculate_visibility_options(category):
    options = [(n, ngettext('From {} category above',
                            'From {} categories above', n).format(n) + ' ' + '\u2192 "{}"'.format(title))
               for n, title in enumerate(category.chain_titles[::-1])]
    options[-1] = (None, _("From everywhere"))
    options[0] = (0, _("Invisible"))
    options[1] = (1, _("From this category only"))

    return options


class CategorySettingsForm(IndicoForm):
    title = StringField(_("Title"), [DataRequired()])
    description = IndicoMarkdownField(_("Description"),
                                      description=_("You can use Markdown or basic HTML formatting tags."))
    timezone = IndicoTimezoneSelectField(_("Timezone"), [DataRequired()],
                                         description=_("Default timezone event lists will show up in. It will also be "
                                                       "used as a default for new events."))
    lecture_theme = IndicoThemeSelectField('simple_event', _("Theme for Lectures"), [DataRequired()],
                                           description=_("Default timetable theme used for lecture events"))
    meeting_theme = IndicoThemeSelectField('meeting', _("Theme for Meetings"), [DataRequired()],
                                           description=_("Default timetable theme used for meeting events"))
    visibility = SelectField(_("Event visibility"), coerce=lambda x: None if x is None else int(x),
                             description=_("""From which point in the category tree contents will be visible from """
                                           """(number of categories upwards). Applies to "Today's events" and """
                                           """Calendar. If the category is moved, this number will be preserved."""))
    event_message_mode = IndicoEnumSelectField(_("Message Type"), enum=EventMessageMode,
                                               default=EventMessageMode.disabled,
                                               description=_("This message will show up at the top of every event page "
                                                             "in this category"))
    event_message = IndicoMarkdownField(_("Content"),
                                        description=_("You can use Markdown or basic HTML formatting tags."))
    event_creation_notification_emails = EmailListField(_("Notification E-mails"),
                                                        description=_("List of e-mails that will receive a notification"
                                                                      " every time a new event is created. One e-mail "
                                                                      "per line."))

    def _validate_visibility(form, field):
        if field.data is not None and not isinstance(field.data, int):
            raise ValidationError('Visibility should be either an integer or None')

    def __init__(self, *args, **kwargs):
        super(CategorySettingsForm, self).__init__(*args, **kwargs)
        category = kwargs.pop('category')
        self.visibility.choices = calculate_visibility_options(category)
        self.visibility.default = ((category.parent.visibility + 1) if
                                   (category.parent and category.parent.visibility is not None) else None)


class CategoryIconForm(IndicoForm):
    icon = JSONField("Icon", widget=DropzoneWidget(accepted_file_types='image/jpeg,image/jpg,image/png,image/gif',
                                                   max_files=1, submit_form=False, submit_if_empty=False,
                                                   add_remove_links=False, handle_flashes=True),
                     description=_("Small icon that will show up next to category names in overview pages. Will be "
                                   "automatically resized if larger than 16x16 pixels."))

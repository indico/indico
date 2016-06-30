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

from flask import request
from wtforms.fields import BooleanField, SelectField, StringField, HiddenField, IntegerField
from wtforms.validators import DataRequired, Optional, InputRequired, NumberRange, ValidationError

from indico.modules.categories.models.categories import EventMessageMode, Category
from indico.modules.events import Event
from indico.util.i18n import _, ngettext
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import (AccessControlListField, PrincipalListField, IndicoProtectionField,
                                     IndicoEnumSelectField, IndicoMarkdownField, IndicoThemeSelectField,
                                     IndicoTimezoneSelectField, EmailListField, JSONField, HiddenFieldList,
                                     MultipleItemsField)
from indico.web.forms.widgets import DropzoneWidget, SwitchWidget, HiddenCheckbox


def calculate_visibility_options(category):
    options = [(n + 1, (ngettext('From category above',
                                 'From {} categories above', n).format(n) + ' ' +
                        '\N{RIGHTWARDS ARROW} "{}"'.format(title)))
               for n, title in enumerate(category.chain_titles[::-1])]
    options.insert(0, (0, _("Invisible")))
    options[1] = (1, _("From this category only"))
    options[-1] = ('', _("From everywhere"))
    return options


class CategorySettingsForm(IndicoForm):
    BASIC_FIELDS = ('title', 'description', 'timezone', 'lecture_theme', 'meeting_theme', 'visibility',
                    'suggestions_disabled', 'event_creation_notification_emails')
    EVENT_HEADER_FIELDS = ('event_message_mode', 'event_message')

    title = StringField(_("Title"), [DataRequired()])
    description = IndicoMarkdownField(_("Description"))
    timezone = IndicoTimezoneSelectField(_("Timezone"), [DataRequired()],
                                         description=_("Default timezone event lists will show up in. It will also be "
                                                       "used as a default for new events."))
    lecture_theme = IndicoThemeSelectField('simple_event', _("Theme for Lectures"), [DataRequired()],
                                           description=_("Default timetable theme used for lecture events"))
    meeting_theme = IndicoThemeSelectField('meeting', _("Theme for Meetings"), [DataRequired()],
                                           description=_("Default timetable theme used for meeting events"))
    visibility = SelectField(_("Event visibility"), [Optional()], coerce=lambda x: None if x == '' else int(x),
                             description=_("""From which point in the category tree contents will be visible from """
                                           """(number of categories upwards). Applies to "Today's events" and """
                                           """Calendar. If the category is moved, this number will be preserved."""))
    suggestions_disabled = BooleanField(_('Disable Suggestions'), widget=SwitchWidget(),
                                        description=_("Enable this if you don't want Indico to suggest this category as"
                                                      " a possible addition to a user's favourites."))
    event_message_mode = IndicoEnumSelectField(_("Message Type"), enum=EventMessageMode,
                                               default=EventMessageMode.disabled,
                                               description=_("This message will show up at the top of every event page "
                                                             "in this category"))
    event_message = IndicoMarkdownField(_("Content"))
    event_creation_notification_emails = EmailListField(_("Notification E-mails"),
                                                        description=_("List of e-mails that will receive a notification"
                                                                      " every time a new event is created. One e-mail "
                                                                      "per line."))

    def __init__(self, *args, **kwargs):
        super(CategorySettingsForm, self).__init__(*args, **kwargs)
        category = kwargs.pop('category')
        self.visibility.choices = calculate_visibility_options(category)


class CategoryIconForm(IndicoForm):
    icon = JSONField("Icon", widget=DropzoneWidget(accepted_file_types='image/jpeg,image/jpg,image/png,image/gif',
                                                   max_files=1, submit_form=False, submit_if_empty=False,
                                                   add_remove_links=False, handle_flashes=True),
                     description=_("Small icon that will show up next to category names in overview pages. Will be "
                                   "automatically resized to 16x16 pixels. This may involve loss of image quality, "
                                   "so try to upload images as close as possible to those dimensions."))


class CategoryLogoForm(IndicoForm):
    logo = JSONField("Logo", widget=DropzoneWidget(accepted_file_types='image/jpeg,image/jpg,image/png,image/gif',
                                                   max_files=1, submit_form=False, submit_if_empty=False,
                                                   add_remove_links=False, handle_flashes=True),
                     description=_("Logo that will show up next to the category description."))


class CategoryProtectionForm(IndicoForm):
    _event_creation_fields = ('event_creation_restricted', 'event_creators', 'event_creation_notification_emails')

    protection_mode = IndicoProtectionField(_('Protection mode'), protected_object=lambda form: form.protected_object)
    acl = AccessControlListField(_('Access control list'), groups=True, allow_external=True, allow_networks=True)
    managers = PrincipalListField(_('Managers'), groups=True)
    own_no_access_contact = StringField(_('No access contact'),
                                        description=_('Contact information shown when someone lacks access to the '
                                                      'category'))
    event_creation_restricted = BooleanField(_('Restricted event creation'), widget=SwitchWidget(),
                                             description=_('Whether the event creation should be restricted '
                                                           'to a list of specific persons'))
    event_creators = PrincipalListField(_('Event creators'), groups=True, allow_external=True,
                                        description=_('Users allowed to create events in this category'))

    def __init__(self, *args, **kwargs):
        self.protected_object = kwargs.pop('category')
        super(CategoryProtectionForm, self).__init__(*args, **kwargs)


class CreateCategoryForm(IndicoForm):
    """Form to create a new Category"""

    title = StringField(_("Title"), [DataRequired()])
    description = IndicoMarkdownField(_("Description"))


class SplitCategoryForm(IndicoForm):
    first_category = StringField(_('Category name #1'), [DataRequired()],
                                 description=_('Selected events will be moved into a new sub-category with this '
                                               'title.'))
    second_category = StringField(_('Category name #2'), [DataRequired()],
                                  description=_('Events that were not selected will be moved into a new sub-category '
                                                'with this title.'))
    event_id = HiddenFieldList()
    all_selected = BooleanField(widget=HiddenCheckbox())
    submitted = HiddenField()

    def __init__(self, *args, **kwargs):
        super(SplitCategoryForm, self).__init__(*args, **kwargs)
        if self.all_selected.data:
            self.event_id.data = []
            self.first_category.label.text = _('Category name')
            self.first_category.description = _('The events will be moved into a new sub-category with this title.')
            del self.second_category

    def is_submitted(self):
        return super(SplitCategoryForm, self).is_submitted() and 'submitted' in request.form


class UpcomingEventsForm(IndicoForm):
    max_entries = IntegerField(_('Max. events'), [InputRequired(), NumberRange(min=0)],
                               description=_("The maximum number of upcoming events to show. Events are sorted by "
                                             "weight so events with a lower weight are more likely to be omitted if "
                                             "there are too many events to show."))
    entries = MultipleItemsField(_('Upcoming events'),
                                 fields=[{'id': 'type', 'caption': _("Type"), 'required': True, 'type': 'select'},
                                         {'id': 'id', 'caption': _("ID"), 'required': True, 'type': 'number',
                                          'step': 1, 'coerce': int},
                                         {'id': 'days', 'caption': _("Days"), 'required': True, 'type': 'number',
                                          'step': 1, 'coerce': int},
                                         {'id': 'weight', 'caption': _("Weight"), 'required': True, 'type': 'number',
                                          'coerce': float}],
                                 choices={'type': {'category': _('Category'), 'event': _('Event')}},
                                 description=_("Specify categories/events shown in the 'upcoming events' list on the "
                                               "home page."))

    def validate_entries(self, field):
        if field.errors:
            return
        for entry in field.data:
            if entry['days'] < 0:
                raise ValidationError(_("'Days' must be a positive integer"))
            if entry['type'] not in {'category', 'event'}:
                raise ValidationError(_('Invalid type'))
            if entry['type'] == 'category' and not Category.get(entry['id'], is_deleted=False):
                raise ValidationError(_('Invalid category: {}').format(entry['id']))
            if entry['type'] == 'event' and not Event.get(entry['id'], is_deleted=False):
                raise ValidationError(_('Invalid event: {}').format(entry['id']))

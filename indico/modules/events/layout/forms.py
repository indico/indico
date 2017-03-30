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

from wtforms.fields import BooleanField, TextAreaField, SelectField
from wtforms.fields.html5 import URLField
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired, Optional, ValidationError

from indico.core.config import Config
from indico.modules.events.layout import theme_settings
from indico.modules.events.layout.util import get_logo_data, get_css_file_data
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import EditableFileField, FileField
from indico.web.forms.validators import UsedIf, HiddenUnless
from indico.web.forms.widgets import CKEditorWidget, SwitchWidget, ColorPickerWidget

THEMES = [('', _('No theme selected')),
          ('orange.css', _('Orange')),
          ('brown.css', _('Brown')),
          ('right_menu.css', _('Right menu'))]


def _get_timetable_theme_choices(event):
    it = ((tid, data['title']) for tid, data in theme_settings.get_themes_for(event.type).viewitems())
    return sorted(it, key=lambda x: x[1].lower())


class ConferenceLayoutForm(IndicoForm):
    is_searchable = BooleanField(_("Enable search"), widget=SwitchWidget(),
                                 description=_("Enable search within the event"))
    show_nav_bar = BooleanField(_("Show navigation bar"), widget=SwitchWidget(),
                                description=_("Show the navigation bar at the top"))
    show_banner = BooleanField(_("\"Now happening\""), widget=SwitchWidget(on_label=_("ON"), off_label=_("OFF")),
                               description=_("Show a banner with the current entries from the timetable"))
    show_social_badges = BooleanField(_("Show social badges"), widget=SwitchWidget())

    # Style
    header_text_color = StringField(_("Text colour"), widget=ColorPickerWidget())
    header_background_color = StringField(_("Background colour"), widget=ColorPickerWidget())

    # Announcement
    announcement = StringField(_("Announcement"),
                               [UsedIf(lambda form, field: form.show_announcement.data)],
                               description=_("Short message shown below the title"))
    show_announcement = BooleanField(_("Show announcement"), widget=SwitchWidget(),
                                     description=_("Show the announcement message"))

    # Timetable
    timetable_by_room = BooleanField(_("Group by room"), widget=SwitchWidget(),
                                     description=_("Group the entries of the timetable by room by default"))
    timetable_detailed = BooleanField(_("Show detailed view"), widget=SwitchWidget(),
                                      description=_("Show the detailed view of the timetable by default."))
    timetable_theme = SelectField(_('Theme'), [Optional()], coerce=lambda x: x or None)
    # Themes
    use_custom_css = BooleanField(_("Use custom CSS"), widget=SwitchWidget(),
                                  description=_("Use a custom CSS file as a theme for the conference page. Deactivate "
                                                "this option to reveal the available Indico themes."))
    theme = SelectField(_("Theme"), [Optional(), HiddenUnless('use_custom_css', False)], choices=THEMES,
                        coerce=lambda x: (x or None),
                        description=_("Currently selected theme of the conference page. Click on the Preview button to "
                                      "preview and select a different one."))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(ConferenceLayoutForm, self).__init__(*args, **kwargs)
        self.timetable_theme.choices = [('', _('Default'))] + _get_timetable_theme_choices(self.event)

    def validate_use_custom_css(self, field):
        if field.data and not self.event.has_stylesheet:
            raise ValidationError(_('Cannot enable custom stylesheet unless there is one.'))


class LectureMeetingLayoutForm(IndicoForm):
    timetable_theme = SelectField(_('Timetable theme'), [DataRequired()])

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event')
        super(LectureMeetingLayoutForm, self).__init__(*args, **kwargs)
        self.timetable_theme.choices = _get_timetable_theme_choices(event)


class LogoForm(IndicoForm):
    logo = EditableFileField("Logo", accepted_file_types='image/jpeg,image/jpg,image/png,image/gif',
                             add_remove_links=False, handle_flashes=True, get_metadata=get_logo_data,
                             description=_("Logo to be displayed next to the event's title"))


class CSSForm(IndicoForm):
    css_file = EditableFileField(_("Custom CSS file"), accepted_file_types='.css', add_remove_links=False,
                                 get_metadata=get_css_file_data, handle_flashes=True)

    def __init__(self, *args, **kwargs):
        super(CSSForm, self).__init__(*args, **kwargs)
        self.css_file.description = _("If you want to fully customize your conference page you can create your own "
                                      "stylesheet and upload it. An example stylesheet can be downloaded "
                                      "<a href='{base_url}/standard.css' target='_blank'>here</a>."
                                      .format(base_url=Config.getInstance().getCssConfTemplateBaseURL()))


class MenuBuiltinEntryForm(IndicoForm):
    custom_title = BooleanField(_("Custom title"), widget=SwitchWidget())
    title = StringField(_("Title"), [HiddenUnless('custom_title'), DataRequired()])
    is_enabled = BooleanField(_("Show"), widget=SwitchWidget())

    def __init__(self, *args, **kwargs):
        entry = kwargs.pop('entry')
        super(MenuBuiltinEntryForm, self).__init__(*args, **kwargs)
        self.custom_title.description = _("If you customize the title, that title is used regardless of the user's "
                                          "language preference.  The default title <strong>{title}</strong> is "
                                          "displayed in the user's language.").format(title=entry.default_data.title)

    def post_validate(self):
        if not self.custom_title.data:
            self.title.data = None


class MenuUserEntryFormBase(IndicoForm):
    title = StringField(_("Title"), [DataRequired()])
    is_enabled = BooleanField(_("Show"), widget=SwitchWidget())
    new_tab = BooleanField(_("Open in a new tab"), widget=SwitchWidget())


class MenuLinkForm(MenuUserEntryFormBase):
    link_url = URLField(_("URL"), [DataRequired()])


class MenuPageForm(MenuUserEntryFormBase):
    html = TextAreaField(_("Content"), [DataRequired()], widget=CKEditorWidget())


class AddImagesForm(IndicoForm):
    image = FileField("Image", multiple_files=True, accepted_file_types='image/jpeg,image/jpg,image/png,image/gif')


class CSSSelectionForm(IndicoForm):
    theme = SelectField(_("Theme"), [Optional()], coerce=lambda x: x)

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event')
        super(CSSSelectionForm, self).__init__(*args, **kwargs)
        self.theme.choices = list(THEMES)
        if event.has_stylesheet:
            custom = [('_custom', _("Custom CSS file ({name})").format(name=event.stylesheet_metadata['filename']))]
            self.theme.choices = THEMES + custom

# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from wtforms.fields import BooleanField, SelectField, TextAreaField
from wtforms.fields.html5 import URLField
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired, Optional, ValidationError

from indico.core.config import config
from indico.modules.events.layout import theme_settings
from indico.modules.events.layout.util import get_css_file_data, get_logo_data, get_plugin_conference_themes
from indico.modules.users import NameFormat
from indico.util.i18n import _, orig_string
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import EditableFileField, FileField, IndicoEnumSelectField
from indico.web.forms.validators import HiddenUnless, UsedIf
from indico.web.forms.widgets import CKEditorWidget, ColorPickerWidget, SwitchWidget


THEMES = [('', _('No theme selected')),
          ('orange.css', _('Orange')),
          ('brown.css', _('Brown')),
          ('right_menu.css', _('Right menu'))]


def _get_timetable_theme_choices(event):
    it = ((tid, data['title']) for tid, data in theme_settings.get_themes_for(event.type).viewitems())
    return sorted(it, key=lambda x: x[1].lower())


def _get_conference_theme_choices():
    plugin_themes = [(k, v[1]) for k, v in get_plugin_conference_themes().iteritems()]
    return THEMES + sorted(plugin_themes, key=lambda x: x[1].lower())


class LoggedLayoutForm(IndicoForm):
    @classmethod
    def build_field_metadata(cls, field):
        if field.short_name == 'name_format':
            return {'title': orig_string(field.label.text),
                    'default': orig_string(field.none)}
        elif field.short_name == 'theme':
            choices = {(k or None): orig_string(v) for k, v in field.choices}
            return {'title': orig_string(field.label.text),
                    'type': 'string',
                    'convert': lambda changes: [choices.get(x) for x in changes]}
        elif field.short_name == 'timetable_theme':
            choices = {(k or None): v for k, v in field.choices}
            return {'title': orig_string(field.label.text),
                    'type': 'string',
                    'convert': lambda changes: [choices.get(x) for x in changes]}
        else:
            return orig_string(field.label.text)

    @property
    def log_fields_metadata(self):
        return {k: self.build_field_metadata(v) for k, v in self._fields.iteritems()}


class ConferenceLayoutForm(LoggedLayoutForm):
    is_searchable = BooleanField(_("Enable search"), widget=SwitchWidget(),
                                 description=_("Enable search within the event"))
    show_nav_bar = BooleanField(_("Show navigation bar"), widget=SwitchWidget(),
                                description=_("Show the navigation bar at the top"))
    show_banner = BooleanField(_("\"Now happening\""), widget=SwitchWidget(),
                               description=_("Show a banner with the current entries from the timetable"))
    show_social_badges = BooleanField(_("Show social badges"), widget=SwitchWidget())
    name_format = IndicoEnumSelectField(_('Name format'), enum=NameFormat, none=_('Inherit from user preferences'),
                                        description=_('Format in which names are displayed'))

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
    theme = SelectField(_("Theme"), [Optional(), HiddenUnless('use_custom_css', False)],
                        coerce=lambda x: (x or None),
                        description=_("Currently selected theme of the conference page. Click on the Preview button to "
                                      "preview and select a different one."))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(ConferenceLayoutForm, self).__init__(*args, **kwargs)
        self.timetable_theme.choices = [('', _('Default'))] + _get_timetable_theme_choices(self.event)
        self.theme.choices = _get_conference_theme_choices()

    def validate_use_custom_css(self, field):
        if field.data and not self.event.has_stylesheet:
            raise ValidationError(_('Cannot enable custom stylesheet unless there is one.'))


class LectureMeetingLayoutForm(LoggedLayoutForm):
    name_format = IndicoEnumSelectField(_('Name format'), enum=NameFormat, none=_('Inherit from user preferences'),
                                        description=_('Format in which names are displayed'))
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
                                      .format(base_url=config.CONFERENCE_CSS_TEMPLATES_BASE_URL))


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
    registered_only = BooleanField(_("Restricted"), widget=SwitchWidget(),
                                   description=_("Visible to registered users only."))


class MenuLinkForm(MenuUserEntryFormBase):
    link_url = URLField(_("URL"), [DataRequired()])


class MenuPageForm(MenuUserEntryFormBase):
    html = TextAreaField(_("Content"), [DataRequired()], widget=CKEditorWidget())


class AddImagesForm(IndicoForm):
    image = FileField("Image", multiple_files=True, accepted_file_types='image/jpeg,image/jpg,image/png,image/gif')


class CSSSelectionForm(IndicoForm):
    theme = SelectField(_("Theme"), [Optional()], coerce=lambda x: (x or None))

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event')
        super(CSSSelectionForm, self).__init__(*args, **kwargs)
        self.theme.choices = _get_conference_theme_choices()
        if event.has_stylesheet:
            custom = [('_custom', _("Custom CSS file ({name})").format(name=event.stylesheet_metadata['filename']))]
            self.theme.choices += custom

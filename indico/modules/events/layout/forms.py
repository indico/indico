# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from wtforms.fields import BooleanField, SelectField, TextAreaField, URLField
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired, Optional, ValidationError

from indico.core.config import config
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.events.layout import theme_settings
from indico.modules.events.layout.models.menu import MenuEntry
from indico.modules.events.layout.util import get_css_file_data, get_logo_data, get_plugin_conference_themes
from indico.modules.users import NameFormat
from indico.util.i18n import _, orig_string
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import EditableFileField, FileField, IndicoEnumSelectField, IndicoProtectionField
from indico.web.forms.fields.principals import PrincipalListField
from indico.web.forms.validators import HiddenUnless, UsedIf
from indico.web.forms.widgets import ColorPickerWidget, SwitchWidget, TinyMCEWidget


THEMES = [('', _('No theme selected')),
          ('orange.css', _('Orange')),
          ('brown.css', _('Brown')),
          ('right_menu.css', _('Right menu'))]


def _get_timetable_theme_choices(event):
    it = ((tid, data['title']) for tid, data in theme_settings.get_themes_for(event.type).items())
    return sorted(it, key=lambda x: x[1].lower())


def _get_conference_theme_choices():
    plugin_themes = [(k, v.title) for k, v in get_plugin_conference_themes().items()]
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
        return {k: self.build_field_metadata(v) for k, v in self._fields.items()}


class ConferenceLayoutForm(LoggedLayoutForm):
    is_searchable = BooleanField(_('Enable search'), widget=SwitchWidget(),
                                 description=_('Enable search within the event'))
    show_nav_bar = BooleanField(_('Show navigation bar'), widget=SwitchWidget(),
                                description=_('Show the navigation bar at the top'))
    show_banner = BooleanField(_('"Now happening"'), widget=SwitchWidget(),
                               description=_('Show a banner with the current entries from the timetable'))
    show_social_badges = BooleanField(_('Show social badges'), widget=SwitchWidget())
    name_format = IndicoEnumSelectField(_('Name format'), enum=NameFormat, none=_('Inherit from user preferences'),
                                        description=_('Format in which names are displayed'))
    show_vc_rooms = BooleanField(_('Show videoconferences'), widget=SwitchWidget(),
                                 description=_('Show videoconferences on the main conference page'))

    # Style
    header_text_color = StringField(_('Text color'), widget=ColorPickerWidget())
    header_background_color = StringField(_('Background color'), widget=ColorPickerWidget())

    # Announcement
    announcement = StringField(_('Announcement'),
                               [UsedIf(lambda form, field: form.show_announcement.data)],
                               description=_('Short message shown below the title'))
    show_announcement = BooleanField(_('Show announcement'), widget=SwitchWidget(),
                                     description=_('Show the announcement message'))

    # Timetable
    timetable_by_room = BooleanField(_('Group by room'), widget=SwitchWidget(),
                                     description=_('Group the entries of the timetable by room by default'))
    timetable_detailed = BooleanField(_('Show detailed view'), widget=SwitchWidget(),
                                      description=_('Show the detailed view of the timetable by default.'))
    timetable_theme = SelectField(_('Theme'), [Optional()], coerce=lambda x: x or None)
    # Themes
    use_custom_css = BooleanField(_('Use custom CSS'), widget=SwitchWidget(),
                                  description=_('Use a custom CSS file as a theme for the conference page. Deactivate '
                                                'this option to reveal the available Indico themes.'))
    theme = SelectField(_('Theme'), [Optional(), HiddenUnless('use_custom_css', False)],
                        coerce=lambda x: (x or None),
                        description=_('Currently selected theme of the conference page. Click on the Preview button to '
                                      'preview and select a different one.'))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super().__init__(*args, **kwargs)
        self.timetable_theme.choices = [('', _('Default')), *_get_timetable_theme_choices(self.event)]
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
        super().__init__(*args, **kwargs)
        self.timetable_theme.choices = _get_timetable_theme_choices(event)


class LogoForm(IndicoForm):
    logo = EditableFileField('Logo', accepted_file_types='image/jpeg,image/jpg,image/png,image/gif',
                             add_remove_links=False, handle_flashes=True, get_metadata=get_logo_data,
                             description=_("Logo to be displayed next to the event's title"))


class CSSForm(IndicoForm):
    css_file = EditableFileField(_('Custom CSS file'), accepted_file_types='.css', add_remove_links=False,
                                 get_metadata=get_css_file_data, handle_flashes=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        url = f'{config.CONFERENCE_CSS_TEMPLATES_BASE_URL}/standard.css'
        link = f"<a href='{url}' target='_blank'>"
        self.css_file.description = _('If you want to fully customize your conference page you can create your own '
                                      'stylesheet and upload it. An example stylesheet can be downloaded '
                                      '{link}here{endlink}').format(link=link, endlink='</a>')


class MenuBuiltinEntryForm(IndicoForm):
    custom_title = BooleanField(_('Custom title'), widget=SwitchWidget())
    title = StringField(_('Title'), [HiddenUnless('custom_title'), DataRequired()])
    is_enabled = BooleanField(_('Show'), widget=SwitchWidget())

    def __init__(self, *args, **kwargs):
        entry = kwargs.pop('entry')
        super().__init__(*args, **kwargs)
        self.custom_title.description = _("If you customize the title, that title is used regardless of the user's "
                                          'language preference.  The default title <strong>{title}</strong> is '
                                          "displayed in the user's language.").format(title=entry.default_data.title)

    def post_validate(self):
        if not self.custom_title.data:
            self.title.data = None


class MenuUserEntryFormBase(IndicoForm):
    title = StringField(_('Title'), [DataRequired()])
    is_enabled = BooleanField(_('Show'), widget=SwitchWidget())
    new_tab = BooleanField(_('Open in a new tab'), widget=SwitchWidget())
    protection_mode = IndicoProtectionField(_('Protection mode'), protected_object=lambda form: form.protected_object)
    acl = PrincipalListField(
        _('Access control list'),
        [HiddenUnless('protection_mode', ProtectionMode.protected, preserve_data=True)],
        event=lambda form: form.event,
        allow_groups=True,
        allow_event_roles=True,
        allow_category_roles=True,
        allow_registration_forms=True,
    )
    speakers_can_access = BooleanField(
        _('Grant speakers access'),
        [HiddenUnless('protection_mode', ProtectionMode.protected, preserve_data=True)],
        widget=SwitchWidget(),
        description=_('In addition to anyone listed in the Access control list, speakers will have access.'),
    )

    def __init__(self, *args, event, **kwargs):
        self.event = event
        self.protected_object = kwargs.get('entry', MenuEntry(event=event))
        super().__init__(*args, **kwargs)

    def __iter__(self):
        # keep acl fields last when rendering the form
        return iter(sorted(super().__iter__(),
                           key=lambda x: x.short_name in ('protection_mode', 'acl', 'speakers_can_access')))


class MenuLinkForm(MenuUserEntryFormBase):
    link_url = URLField(_('URL'), [DataRequired()])


class MenuPageForm(MenuUserEntryFormBase):
    html = TextAreaField(_('Content'), [DataRequired()], widget=TinyMCEWidget(images=True))

    def __init__(self, *args, editor_upload_url, **kwargs):
        self.editor_upload_url = editor_upload_url
        super().__init__(*args, **kwargs)


class AddImagesForm(IndicoForm):
    image = FileField('Image', multiple_files=True, accepted_file_types='image/jpeg,image/jpg,image/png,image/gif')


class CSSSelectionForm(IndicoForm):
    theme = SelectField(_('Theme'), [Optional()], coerce=lambda x: (x or None))

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event')
        super().__init__(*args, **kwargs)
        self.theme.choices = _get_conference_theme_choices()
        if event.has_stylesheet:
            custom = [('_custom', _('Custom CSS file ({name})').format(name=event.stylesheet_metadata['filename']))]
            self.theme.choices += custom

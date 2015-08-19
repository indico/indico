# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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
from wtforms.fields.simple import StringField, HiddenField
from wtforms.validators import InputRequired, DataRequired

from indico.modules.events.layout.models.stylesheets import StylesheetFile
from indico.modules.events.layout.util import get_css_url
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import JSONField
from indico.web.forms.validators import UsedIf, HiddenUnless
from indico.web.forms.widgets import CKEditorWidget, SwitchWidget, ColorPickerWidget, DropzoneWidget

THEMES = [('', _('No theme selected')),
          ('orange.css', _('Orange')),
          ('brown.css', _('Brown')),
          ('right_menu.css', _('Right menu')),
          ('template_indico.css', _('Indico default')),
          ('template0.css', _('Template 0'))]


class LayoutForm(IndicoForm):
    is_searchable = BooleanField(_("Enable search"), widget=SwitchWidget(),
                                 description=_("Enable search within the event"))
    show_nav_bar = BooleanField(_("Show navigation bar"), widget=SwitchWidget(),
                                description=_("Show the navigation bar at the top"))
    show_banner = BooleanField(_("\"Now happening\""), widget=SwitchWidget(on_label=_("ON"), off_label=_("OFF")),
                               description=_("Show a banner with the current entries from the timetable"))
    show_social_badges = BooleanField(_("Show social badges"), widget=SwitchWidget())

    # Style
    logo = JSONField("Logo", widget=DropzoneWidget(accepted_file_types='image/*', max_files=1, submit_form=True),
                     description=_("Logo to be displayed next to the event's title"))
    header_text_color = StringField(_("Text colour"), widget=ColorPickerWidget())
    header_background_color = StringField(_("Background colour"), widget=ColorPickerWidget())

    # Announcement
    announcement = StringField(_("Announcement"),
                               [UsedIf(lambda form, field: form.show_announcement.data)],
                               description=_("Short message shown below the title"))
    show_announcement = BooleanField(_("Show announcement"), widget=SwitchWidget(),
                                     description=_("Show the announcement message"))
    css_file = HiddenField(_("Custom CSS file"),
                           widget=DropzoneWidget(accepted_file_types='.css', max_files=1, submit_form=True))
    use_custom_css = BooleanField(_("Use custom CSS"), widget=SwitchWidget(),
                                  description=_("Use a custom CSS file as a theme for the conference page. Deactivate "
                                                "this option to reveal the available Indico themes."))
    theme = SelectField(_("Selected theme"), [HiddenUnless('use_custom_css', False)],
                        description=_("Currently selected theme of the conference page. Click on the Preview button to "
                                      "preview and select a different one."))

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event')
        super(LayoutForm, self).__init__(*args, **kwargs)
        self.css_file.description = _("If you want to fully customize your conference page you can create your own "
                                      "stylesheet and upload it. An example stylesheet can be downloaded "
                                      "<a href='{url}'>here</a>.".format(url=get_css_url('standard.css')))
        self.logo.widget.options['url'] = url_for('event_layout.logo_upload', event)
        self.css_file.widget.options['url'] = url_for('event_layout.css_upload', event)
        css_file = StylesheetFile.find(StylesheetFile.event_id == event.id).first()
        self.theme.choices = list(THEMES)
        if css_file:
            self.theme.choices = (THEMES +
                                  [('_custom', _("Custom CSS file ({file_name})".format(file_name=css_file.filename)))])


class MenuEntryForm(IndicoForm):
    title = StringField(_("Title"), [InputRequired()])
    is_enabled = BooleanField(_("Show"), widget=SwitchWidget())


class MenuUserEntry(MenuEntryForm):
    new_tab = BooleanField(_("Open in a new tab"), widget=SwitchWidget())


class MenuLinkForm(MenuUserEntry):
    endpoint = URLField(_("URL"), [DataRequired()])


class MenuPageForm(MenuUserEntry):
    html = TextAreaField(_("Content"), [DataRequired()], widget=CKEditorWidget())


class AddImagesForm(IndicoForm):
    image = JSONField("Image", widget=DropzoneWidget(accepted_file_types='image/*'))


class CSSSelectionForm(IndicoForm):
    theme = SelectField(_("Theme"))

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event')
        super(CSSSelectionForm, self).__init__(*args, **kwargs)
        css_file = StylesheetFile.find_first(event_id=event.id)
        self.theme.choices = list(THEMES)
        if css_file:
            self.theme.choices = (THEMES +
                                  [('_custom', _("Custom CSS file ({file_name})".format(file_name=css_file.filename)))])

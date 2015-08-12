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

from wtforms.fields import BooleanField, TextAreaField
from wtforms.fields.html5 import URLField
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired, InputRequired

from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import JSONField
from indico.web.forms.validators import UsedIf
from indico.web.forms.widgets import CKEditorWidget, SwitchWidget, ColorPickerWidget, DropzoneWidget


class LayoutForm(IndicoForm):
    is_searchable = BooleanField(_("Enable search"), widget=SwitchWidget(),
                                 description=_("Enable search within the event"))
    show_nav_bar = BooleanField(_("Show navigation bar"), widget=SwitchWidget(),
                                description=_("Show the navigation bar at the top"))
    show_banner = BooleanField(_("\"Now happening\""), widget=SwitchWidget(on_label=_("ON"), off_label=_("OFF")),
                               description=_("Show a banner with the current entries from the timetable"))
    show_social_badges = BooleanField(_("Show social badges"), widget=SwitchWidget())

    # Style
    logo = JSONField("Logo", widget=DropzoneWidget(accepted_files='image/*'),
                     description=_("Logo to be displayed next to the event's title"))
    header_text_color = StringField(_("Text colour"), widget=ColorPickerWidget())
    header_background_color = StringField(_("Background colour"), widget=ColorPickerWidget())

    # Announcement
    announcement = StringField(_("Announcement"),
                               [UsedIf(lambda form, field: form.show_announcement.data), DataRequired()],
                               description=_("Short message shown below the title"))
    show_announcement = BooleanField(_("Show announcement"), widget=SwitchWidget(),
                                     description=_("Show the announcement message"))

    def __init__(self, *args, **kwargs):
        super(LayoutForm, self).__init__(*args, **kwargs)
        event = kwargs.pop('event')
        self.logo.widget.post_url = url_for('event_layout.logo-upload', event)


class MenuEntryForm(IndicoForm):
    title = StringField(_("Title"), [InputRequired()])
    visible = BooleanField(_("Show"), widget=SwitchWidget())


class MenuUserEntry(MenuEntryForm):
    new_tab = BooleanField(_("Open in a new tab"), widget=SwitchWidget())


class MenuLinkForm(MenuUserEntry):
    endpoint = URLField(_("URL"))


class MenuPageForm(MenuUserEntry):
    html = TextAreaField(_("Content"), widget=CKEditorWidget())

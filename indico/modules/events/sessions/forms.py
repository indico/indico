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

from datetime import timedelta

from wtforms.fields import StringField, BooleanField, TextAreaField
from wtforms.validators import DataRequired

from indico.modules.events.sessions.util import get_colors
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import (IndicoPalettePickerField, TimeDeltaField, IndicoLocationField, PrincipalListField,
                                     IndicoProtectionField)
from indico.web.forms.widgets import SwitchWidget
from indico.web.forms.validators import UsedIf


class SessionForm(IndicoForm):
    title = StringField(_('Title'), [DataRequired()], description=_('Title of the session'))
    code = StringField(_('Session code'), description=_('Code of the session'))
    description = TextAreaField(_('Description'), description=_('Text describing the session'))
    default_contribution_duration = TimeDeltaField(_('Default contribution duration'), units=('minutes', 'hours'),
                                                   description=_('Specify the default duration of contributions '
                                                                 'within the session'),
                                                   default=timedelta(minutes=20))
    location_data = IndicoLocationField(_("Location"),
                                        description=_("Default location for blocks inside the session."))
    colors = IndicoPalettePickerField(_('Colours'), color_list=get_colors(),
                                      description=_('Specify text and background colours for the session.'))
    is_poster = BooleanField(_('Poster session'), widget=SwitchWidget(),
                             description=_('Whether the session is a poster session.'))

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event')
        super(SessionForm, self).__init__(*args, **kwargs)
        if event.type != 'conference':
            del self.is_poster


class SessionProtectionForm(IndicoForm):
    protection_mode = IndicoProtectionField(_('Protection mode'))
    acl = PrincipalListField(_('Access control list'), [UsedIf(lambda form, field: form.protected_object.is_protected)],
                             serializable=False, groups=True,
                             description=_('List of users allowed to access the session. If the protection mode '
                                           'is set to inheriting, these users have access in addition to the users '
                                           'who can access the parent object.'))
    managers = PrincipalListField(_('Managers'), serializable=False, groups=True,
                                  description=_('List of users allowed to modify the session'))
    coordinators = PrincipalListField(_('Coordinators'), serializable=False, groups=True)

    def __init__(self, *args, **kwargs):
        self.protected_object = kwargs.pop('session')
        super(SessionProtectionForm, self).__init__(*args, **kwargs)

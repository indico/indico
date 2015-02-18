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
import re

from flask import render_template

from wtforms.fields.core import BooleanField
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired, Length, Regexp

from indico.util.decorators import classproperty
from indico.util.i18n import _
from indico.util.user import retrieve_principals
from indico.web.flask.templating import get_overridable_template_name
from indico.web.forms.base import IndicoForm, FormDefaults
from indico.web.forms.fields import PrincipalField

ROOM_NAME_RE = re.compile(r'[\w\-]+')
PREFIX_RE = re.compile('^vc_')


class VCPluginSettingsFormBase(IndicoForm):
    managers = PrincipalField(_('Managers'), description=_('Service managers'))
    acl = PrincipalField(_('ACL'), groups=True,
                         description=_('Users and Groups authorised to create video conference rooms'))
    notify_managers = BooleanField(_('Notify managers'),
                                   description=_('Send email notifications to managers'))


class VCPluginMixin(object):
    settings_form = VCPluginSettingsFormBase
    #: the :class:`IndicoForm` to use for the video conference room form
    vc_room_form = None
    #: default values to use

    def init(self):
        super(VCPluginMixin, self).init()
        if not self.name.startswith('vc_'):
            raise Exception('Video conference plugins must be named vc_*')

    def get_vc_room_form_defaults(self, event):
        return {}

    @property
    def service_name(self):
        return PREFIX_RE.sub('', self.name)

    @classproperty
    @classmethod
    def category(self):
        from indico.core.plugins import PluginCategory
        return PluginCategory.videoconference

    def render_form(self, **kwargs):
        """Renders the video conference room form
        :param kwargs: arguments passed to the template
        """
        tpl = get_overridable_template_name('manage_event_create_room.html', self, 'vc/')
        return render_template(tpl, **kwargs)

    def render_custom_create_button(self, **kwargs):
        tpl = get_overridable_template_name('create_button.html', self, 'vc/')
        return render_template(tpl, plugin=self, **kwargs)

    def create_form(self, event, existing_vc_room=None):
        """Creates the video conference room form
        :param event: the event the video conference room is for
        :return: an instance of an :class:`IndicoForm` subclass
        """
        if existing_vc_room:
            defaults = FormDefaults(existing_vc_room.data, name=existing_vc_room.name)
        else:
            defaults = FormDefaults(self.get_vc_room_form_defaults(event))
        with self.plugin_context():
            return self.vc_room_form(prefix='vc-', obj=defaults, event=event, vc_room=existing_vc_room)

    def can_manage_vc_rooms(self, user, event):
        acl = self.settings.get('acl')
        if not acl:
            return True

        principals = retrieve_principals(acl)
        return any(principal.containsUser(user) for principal in principals)


class VCRoomFormBase(IndicoForm):
    name = StringField(_('Name'), [DataRequired(), Length(min=3, max=60), Regexp(ROOM_NAME_RE)],
                       description=_('The name of the room'))

    def __init__(self, *args, **kwargs):
        self.vc_room = kwargs.pop('vc_room')
        self.event = kwargs.pop('event')
        super(VCRoomFormBase, self).__init__(*args, **kwargs)

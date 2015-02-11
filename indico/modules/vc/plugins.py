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

from flask import render_template
from flask_pluginengine import render_plugin_template, plugin_context

from wtforms.fields.core import BooleanField

from indico.util.decorators import classproperty
from indico.util.i18n import _
from indico.web.flask.templating import get_overridable_template_name
from indico.web.forms.base import IndicoForm, FormDefaults
from indico.web.forms.fields import PrincipalField


class VCPluginSettingsFormBase(IndicoForm):
    admins = PrincipalField(_('Administrators'), description=_('Vidyo admins / responsibles'))
    authorized_users = PrincipalField(_('Authorized users'),
                                      description=_('Users and Groups authorised to create Vidyo bookings'))
    notify_admins = BooleanField(_('Notify admins'),
                                 description=_('Should Vidyo administrators receive email notifications?'))
    bookings_search = BooleanField(_('Search for bookings is allowed'))


class VCPluginMixin(object):
    settings_form = VCPluginSettingsFormBase
    #: the :class:`IndicoForm` to use for the video conference room form
    vc_room_form = None
    #: default values to use
    vc_room_form_defaults = {}

    def init(self):
        super(VCPluginMixin, self).init()
        if not self.name.startswith('vc_'):
            raise Exception('Video conference plugins must be named vc_*')

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

    def create_form(self, event, existing_vc_room=None):
        """Creates the video conference room form
        :param event: the event the video conference room is for
        :return: an instance of an :class:`IndicoForm` subclass
        """
        defaults = FormDefaults(existing_vc_room.data if existing_vc_room else self.vc_room_form_defaults)
        with self.plugin_context():
            return self.vc_room_form(prefix='vc-', obj=defaults, event=event)

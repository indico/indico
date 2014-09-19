## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico; if not, see <http://www.gnu.org/licenses/>.

from flask import request, flash, redirect

from indico.core.plugins import plugin_engine
from indico.core.plugins.views import WPPlugins
from MaKaC.webinterface.rh.admins import RHAdminBase
from indico.modules.rb.forms.base import FormDefaults
from indico.util.i18n import _


class RHPlugins(RHAdminBase):
    def _process(self):
        return WPPlugins.render_template('index.html', active_plugins=plugin_engine.get_active_plugins())


class RHPluginDetails(RHAdminBase):
    def _checkParams(self):
        self.plugin = plugin_engine.get_plugin(request.view_args['plugin'])

    def _process(self):
        plugin = self.plugin
        form = None
        if plugin.settings_form:
            defaults = FormDefaults(**plugin.settings.get_all())
            form = plugin.settings_form(obj=defaults)
            if form.validate_on_submit():
                plugin.settings.set_multi(form.data)
                flash(_(u'Settings saved'), 'success')
                return redirect(request.url)
        return WPPlugins.render_template('details.html', plugin=plugin, form=form)

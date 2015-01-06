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
from werkzeug.exceptions import NotFound

from collections import defaultdict, OrderedDict

from indico.core.plugins import plugin_engine
from indico.core.plugins.views import WPPlugins
from indico.web.forms.base import FormDefaults
from indico.util.i18n import _
from MaKaC.webinterface.rh.admins import RHAdminBase


class RHPlugins(RHAdminBase):
    def _process(self):
        plugins = [p for p in plugin_engine.get_active_plugins().viewvalues()]
        categories = defaultdict(list)
        other = []
        for plugin in plugins:
            if plugin.category:
                categories[plugin.category].append(plugin)
            else:
                other.append(plugin)

        # Sort the plugins of each category in alphabetic order and in a way that the internal plugins are always
        # listed in the front
        for category in categories:
            categories[category].sort(key=lambda plug: (not plug.hidden, plug.title))
        ordered_categories = OrderedDict(sorted(categories.items()))
        if other:
            ordered_categories['other'] = other
        return WPPlugins.render_template('index.html', categorized_plugins=ordered_categories)


class RHPluginDetails(RHAdminBase):
    def _checkParams(self):
        self.plugin = plugin_engine.get_plugin(request.view_args['plugin'])
        if not self.plugin or self.plugin.hidden:
            raise NotFound

    def _process(self):
        plugin = self.plugin
        form = None
        with plugin.plugin_context():
            if plugin.settings_form:
                defaults = FormDefaults(**plugin.settings.get_all())
                form = plugin.settings_form(obj=defaults)
                if form.validate_on_submit():
                    plugin.settings.set_multi(form.data)
                    flash(_(u'Settings saved'), 'success')
                    return redirect(request.url)
            return WPPlugins.render_template('details.html', plugin=plugin, form=form)

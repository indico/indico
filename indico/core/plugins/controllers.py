# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from collections import OrderedDict, defaultdict
from operator import attrgetter

from flask import flash, request
from werkzeug.exceptions import NotFound

from indico.core.plugins import PluginCategory, plugin_engine
from indico.core.plugins.views import WPPlugins
from indico.modules.admin import RHAdminBase
from indico.util.i18n import _
from indico.web.flask.util import redirect_or_jsonify, url_for
from indico.web.forms.base import FormDefaults


class RHPluginsBase(RHAdminBase):
    pass


class RHPlugins(RHPluginsBase):
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
            categories[category].sort(key=attrgetter('configurable', 'title'))
        ordered_categories = OrderedDict(sorted(categories.items()))
        if other:
            ordered_categories[PluginCategory.other] = other
        return WPPlugins.render_template('index.html', categorized_plugins=ordered_categories)


class RHPluginDetails(RHPluginsBase):
    back_button_endpoint = 'plugins.index'

    def _process_args(self):
        self.plugin = plugin_engine.get_plugin(request.view_args['plugin'])
        if not self.plugin or not self.plugin.configurable:
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
                    flash(_('Settings saved ({0})').format(plugin.title), 'success')
                    return redirect_or_jsonify(request.url)
            return WPPlugins.render_template('details.html', plugin=plugin, form=form,
                                             back_url=url_for(self.back_button_endpoint))

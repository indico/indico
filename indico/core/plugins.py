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

from flask_pluginengine import PluginEngine, Plugin

from indico.web.flask.wrappers import IndicoBlueprint


class IndicoPlugin(Plugin):
    pass


class IndicoPluginEngine(PluginEngine):
    plugin_class = IndicoPlugin


class IndicoPluginBlueprint(IndicoBlueprint):
    """Like IndicoBlueprint, but it uses its own static folder by default."""

    def __init__(self, name, *args, **kwargs):
        kwargs.setdefault('static_folder', 'static')
        kwargs.setdefault('static_url_path', '/static/{}'.format(name))
        super(IndicoPluginBlueprint, self).__init__(name, *args, **kwargs)


plugin_engine = IndicoPluginEngine()

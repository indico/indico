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

from flask_pluginengine import PluginEngine, Plugin, PluginBlueprintMixin, PluginBlueprintSetupStateMixin

from indico.core import signals
from indico.web.flask.wrappers import IndicoBlueprint, IndicoBlueprintSetupState


class IndicoPlugin(Plugin):
    def init(self):
        self.connect(signals.cli, self.add_cli_command)
        self.connect(signals.shell_context, self.extend_shell_context)
        self.connect(signals.get_blueprints, lambda app: (self, self.get_blueprints()))

    def register_blueprint(self, blueprint):
        if not hasattr(self, '_blueprints'):
            self._blueprints = set()
            self.connect(signals.get_blueprints, lambda app: (self, self._blueprints))
        self._blueprints.add(blueprint)

    def get_blueprints(self):
        """Return blueprints to be registered on the application

        A single blueprint can be returned directly, for multiple blueprint you need
        to yield them.
        """
        pass

    def add_cli_command(self, manager):
        """Add custom commands/submanagers to the manager of the `indico` cli tool."""
        pass

    def extend_shell_context(self, sender, add_to_context):
        """Add custom items to the `indico shell` context."""
        pass


class IndicoPluginEngine(PluginEngine):
    plugin_class = IndicoPlugin


class IndicoPluginBlueprintSetupState(PluginBlueprintSetupStateMixin, IndicoBlueprintSetupState):
    pass


class IndicoPluginBlueprint(PluginBlueprintMixin, IndicoBlueprint):
    def make_setup_state(self, app, options, first_registration=False):
        return IndicoPluginBlueprintSetupState(self, app, options, first_registration)


plugin_engine = IndicoPluginEngine()

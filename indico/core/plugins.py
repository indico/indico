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

import os
from urlparse import urlparse

from flask_pluginengine import (PluginEngine, Plugin, PluginBlueprintMixin, PluginBlueprintSetupStateMixin,
                                current_plugin)
from markupsafe import Markup
from webassets import Environment, Bundle

from indico.core import signals
from indico.core.config import Config
from indico.web.assets import SASS_BASE_MODULES, configure_pyscss
from indico.web.flask.wrappers import IndicoBlueprint, IndicoBlueprintSetupState


class IndicoPlugin(Plugin):
    def init(self):
        self.connect(signals.cli, self.add_cli_command)
        self.connect(signals.shell_context, lambda _, add_to_context: self.extend_shell_context(add_to_context))
        self.connect(signals.get_blueprints, lambda app: (self, self.get_blueprints()))
        self._setup_assets()

    def _setup_assets(self):
        config = Config.getInstance()
        url_base_path = urlparse(config.getBaseURL()).path
        output_dir = os.path.join(self.root_path, 'static')
        url = '{}/static/plugins/{}'.format(url_base_path, self.name)
        self.assets = Environment(output_dir, url, debug=config.getDebug())
        configure_pyscss(self.assets)
        self.register_assets()

    def get_blueprints(self):
        """Return blueprints to be registered on the application

        A single blueprint can be returned directly, for multiple blueprint you need
        to yield them.
        """
        pass

    def add_cli_command(self, manager):
        """Add custom commands/submanagers to the manager of the `indico` cli tool."""
        pass

    def extend_shell_context(self, add_to_context):
        """Add custom items to the `indico shell` context."""
        pass

    def register_assets(self):
        """Add assets to the plugin's webassets environment.

        In most cases the whole method can consist of calls to
        :meth:`register_js_bundle` and :meth:`register_scss_bundle`.
        """
        pass

    def register_js_bundle(self, name, *files):
        """Registers a JS bundle in the plugin's webassets environment"""
        bundle = Bundle(*files, filters='rjsmin', output='js/{}_%(version)s.min.js'.format(name))
        self.assets.register(name, bundle)

    def register_css_bundle(self, name, *files):
        """Registers a SCSS bundle in the plugin's webassets environment"""
        bundle = Bundle(*files,
                        filters=('pyscss', 'cssrewrite', 'cssmin'),
                        output='css/{}_%(version)s.min.css'.format(name),
                        depends=SASS_BASE_MODULES)
        self.assets.register(name, bundle)

    def inject_css(self, name, view_class=None):
        """Injects a CSS bundle into Indico's pages

        :param name: Name of the bundle
        :param view_class: If a WP class is specified, only inject it into pages using that class
        """
        kwargs = {}
        if view_class is not None:
            kwargs['sender'] = view_class
        self.connect(signals.inject_css, lambda _: self.assets[name].urls(), **kwargs)

    def inject_js(self, name, view_class=None):
        """Injects a JS bundle into Indico's pages

        :param name: Name of the bundle
        :param view_class: If a WP class is specified, only inject it into pages using that class
        """
        kwargs = {}
        if view_class is not None:
            kwargs['sender'] = view_class
        self.connect(signals.inject_js, lambda _: self.assets[name].urls(), **kwargs)


def plugin_js_assets(bundle):
    return Markup('\n'.join('<script src="{}"></script>'.format(url)
                            for url in current_plugin.assets[bundle].urls()))


def plugin_css_assets(bundle):
    return Markup('\n'.join('<link rel="stylesheet" type="text/css" href="{}">'.format(url)
                            for url in current_plugin.assets[bundle].urls()))


class IndicoPluginEngine(PluginEngine):
    plugin_class = IndicoPlugin


class IndicoPluginBlueprintSetupState(PluginBlueprintSetupStateMixin, IndicoBlueprintSetupState):
    pass


class IndicoPluginBlueprint(PluginBlueprintMixin, IndicoBlueprint):
    def make_setup_state(self, app, options, first_registration=False):
        return IndicoPluginBlueprintSetupState(self, app, options, first_registration)


plugin_engine = IndicoPluginEngine()

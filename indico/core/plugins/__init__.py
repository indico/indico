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
import re
from urlparse import urlparse

from flask_pluginengine import (PluginEngine, Plugin, PluginBlueprintMixin, PluginBlueprintSetupStateMixin,
                                current_plugin)
from markupsafe import Markup
from webassets import Environment, Bundle

from indico.core import signals
from indico.core.config import Config
from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import import_all_models
from indico.core.models.settings import SettingsProxy
from indico.util.decorators import cached_classproperty
from indico.web.assets import SASS_BASE_MODULES, configure_pyscss
from indico.web.flask.wrappers import IndicoBlueprint, IndicoBlueprintSetupState


class IndicoPlugin(Plugin):
    """Base class for an Indico plugin

    All your plugins need to inherit from this class. It extends the
    `Plugin` class from Flask-PluginEngine with useful indico-specific
    functionality that makes it easier to write custom plugins.

    When creating your plugin, the class-level docstring is used to
    generate the friendly name and description of a plugin. Its first
    line becomes the name while everything else goes into the description.

    This class provides methods for some of the more common hooks Indico
    provides. Additional signals are defined in :mod:`~indico.core.signals`
    and can be connected to custom functions using :meth:`connect`.
    """

    #: WTForm for the plugin's settings. All fields must return JSON-serializable types.
    settings_form = None
    #: A dictionary which can contain the kwargs for a specific field in the `settings_form`.
    settings_form_field_opts = {}

    def init(self):
        """Called when the plugin is being loaded/initialized.

        If you want to run custom initialization code, this is the
        method to override. Make sure to call the base method or
        the other overridable methods in this class will not be
        called anymore.
        """
        self.alembic_versions_path = os.path.join(self.root_path, 'migrations')
        self.connect(signals.cli, self.add_cli_command)
        self.connect(signals.shell_context, lambda _, add_to_context: self.extend_shell_context(add_to_context))
        self.connect(signals.get_blueprints, lambda app: (self, self.get_blueprints()))
        self._setup_assets()
        self._import_models()

    def _setup_assets(self):
        config = Config.getInstance()
        url_base_path = urlparse(config.getBaseURL()).path
        output_dir = os.path.join(self.root_path, 'static')
        url = '{}/static/plugins/{}'.format(url_base_path, self.name)
        self.assets = Environment(output_dir, url, debug=config.getDebug())
        configure_pyscss(self.assets)
        self.register_assets()

    def _import_models(self):
        old_models = set(db.Model._decl_class_registry.items())
        import_all_models(self.package_name)
        added_models = set(db.Model._decl_class_registry.items()) - old_models
        # Ensure that only plugin schemas have been touched. It would be nice if we could actually
        # restrict a plugin to plugin_PLUGNNAME but since we load all models from the plugin's package
        # which could contain more than one plugin this is not easily possible.
        for name, model in added_models:
            schema = model.__table__.schema
            if not schema.startswith('plugin_'):
                raise Exception("Plugin '{}' added a model which is not in a plugin schema ('{}' in '{}')"
                                .format(self.name, name, schema))

    def get_blueprints(self):
        """Return blueprints to be registered on the application

        A single blueprint can be returned directly, for multiple blueprint you need
        to yield them or return an iterable.
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
        :meth:`register_js_bundle` and :meth:`register_css_bundle`.
        """
        pass

    def register_js_bundle(self, name, *files):
        """Registers a JS bundle in the plugin's webassets environment"""
        pretty_name = re.sub(r'_js$', '', name)
        bundle = Bundle(*files, filters='rjsmin', output='js/{}_%(version)s.min.js'.format(pretty_name))
        self.assets.register(name, bundle)

    def register_css_bundle(self, name, *files):
        """Registers an SCSS bundle in the plugin's webassets environment"""
        pretty_name = re.sub(r'_css$', '', name)
        bundle = Bundle(*files,
                        filters=('pyscss', 'cssrewrite', 'cssmin'),
                        output='css/{}_%(version)s.min.css'.format(pretty_name),
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

    @cached_classproperty
    @classmethod
    def settings(cls):
        if cls.name is None:
            raise RuntimeError('Plugin has not been loaded yet')
        return SettingsProxy('plugin_{}'.format(cls.name))


def plugin_js_assets(bundle):
    """Jinja template function to generate HTML tags for a JS asset bundle."""
    return Markup('\n'.join('<script src="{}"></script>'.format(url)
                            for url in current_plugin.assets[bundle].urls()))


def plugin_css_assets(bundle):
    """Jinja template function to generate HTML tags for a CSS asset bundle."""
    return Markup('\n'.join('<link rel="stylesheet" type="text/css" href="{}">'.format(url)
                            for url in current_plugin.assets[bundle].urls()))


class IndicoPluginEngine(PluginEngine):
    plugin_class = IndicoPlugin


class IndicoPluginBlueprintSetupState(PluginBlueprintSetupStateMixin, IndicoBlueprintSetupState):
    pass


class IndicoPluginBlueprint(PluginBlueprintMixin, IndicoBlueprint):
    """The Blueprint class all plugins need to use.

    It contains the necessary logic to run the blueprint's view
    functions inside the correct plugin context and to make the
    static folder work.
    """
    def make_setup_state(self, app, options, first_registration=False):
        return IndicoPluginBlueprintSetupState(self, app, options, first_registration)


plugin_engine = IndicoPluginEngine()

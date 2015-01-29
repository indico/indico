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

import json
import os
import re
from copy import deepcopy
from heapq import heappush
from urlparse import urlparse

from flask_pluginengine import (PluginEngine, Plugin, PluginBlueprintMixin, PluginBlueprintSetupStateMixin,
                                current_plugin, render_plugin_template, wrap_in_plugin_context)
from markupsafe import Markup
from webassets import Environment, Bundle

from indico.core import signals
from indico.core.config import Config
from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import import_all_models
from indico.core.logger import Logger
from indico.core.models.settings import SettingsProxy, EventSettingsProxy
from indico.util.decorators import cached_classproperty, classproperty
from indico.util.i18n import _
from indico.util.signals import values_from_signal
from indico.util.struct.enum import IndicoEnum
from indico.web.assets import SASS_BASE_MODULES, configure_pyscss
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for, url_rule_to_js
from indico.web.flask.wrappers import IndicoBlueprint, IndicoBlueprintSetupState
from MaKaC.webinterface.pages.base import WPJinjaMixin


class PluginCategory(unicode, IndicoEnum):
    search = _('Search')
    synchronization = _('Synchronization')
    payment = _('Payment')
    importers = _('Importers')
    other = _('Other')


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

    #: WTForm for the plugin's settings (requires `configurable=True`).
    #: All fields must return JSON-serializable types.
    settings_form = None
    #: A dictionary which can contain the kwargs for a specific field in the `settings_form`.
    settings_form_field_opts = {}
    #: A dictionary containing default values for settings
    default_settings = {}
    #: A dictionary containing default values for event-specific settings
    default_event_settings = {}
    #: If the plugin should link to a details/config page in the admin interface
    configurable = False
    #: The group category that the plugin belongs to
    category = None
    #: If `settings` and `event_settings` should use strict mode, i.e. only allow keys in
    #: `default_settings` or `default_event_settings`
    strict_settings = False

    def init(self):
        """Called when the plugin is being loaded/initialized.

        If you want to run custom initialization code, this is the
        method to override. Make sure to call the base method or
        the other overridable methods in this class will not be
        called anymore.
        """
        assert self.configurable or not self.settings_form, 'Non-configurable plugin cannot have a settings form'
        self.alembic_versions_path = os.path.join(self.root_path, 'migrations')
        self.connect(signals.plugin.cli, self.add_cli_command)
        self.connect(signals.plugin.shell_context, lambda _, add_to_context: self.extend_shell_context(add_to_context))
        self.connect(signals.plugin.get_blueprints, lambda app: self.get_blueprints())
        self.template_hook('vars-js', self.inject_vars_js)
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

    def connect(self, signal, receiver, **connect_kwargs):
        connect_kwargs['weak'] = False
        func = wrap_in_plugin_context(self, receiver)
        func.indico_plugin = self
        signal.connect(func, **connect_kwargs)

    def get_blueprints(self):
        """Return blueprints to be registered on the application

        A single blueprint can be returned directly, for multiple blueprint you need
        to yield them or return an iterable.
        """
        pass

    def get_vars_js(self):
        """Return a dictionary with variables to be added to vars.js file"""
        return None

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

    def inject_css(self, name, view_class=None, subclasses=True, condition=None):
        """Injects a CSS bundle into Indico's pages

        :param name: Name of the bundle
        :param view_class: If a WP class is specified, only inject it into pages using that class
        :param subclasses: also inject into subclasses of `view_class`
        :param condition: a callable to determine whether to inject or not. only called, when the
                          view_class criterion matches
        """
        self._inject_asset(signals.plugin.inject_css, name, view_class, subclasses, condition)

    def inject_js(self, name, view_class=None, subclasses=True, condition=None):
        """Injects a JS bundle into Indico's pages

        :param name: Name of the bundle
        :param view_class: If a WP class is specified, only inject it into pages using that class
        :param subclasses: also inject into subclasses of `view_class`
        :param condition: a callable to determine whether to inject or not. only called, when the
                          view_class criterion matches
        """
        self._inject_asset(signals.plugin.inject_js, name, view_class, subclasses, condition)

    def _inject_asset(self, signal, name, view_class=None, subclasses=True, condition=None):
        """Injects an asset bundle into Indico's pages

        :param signal: the signal to use for injection
        :param name: Name of the bundle
        :param view_class: If a WP class is specified, only inject it into pages using that class
        :param subclasses: also inject into subclasses of `view_class`
        :param condition: a callable to determine whether to inject or not. only called, when the
                          view_class criterion matches
        """

        def _do_inject(sender):
            if condition is None or condition():
                return self.assets[name].urls()

        if view_class is None:
            self.connect(signal, _do_inject)
        elif not subclasses:
            self.connect(signal, _do_inject, sender=view_class)
        else:
            def _func(sender):
                if issubclass(sender, view_class):
                    return _do_inject(sender)

            self.connect(signal, _func)

    def inject_vars_js(self):
        """Returns a string that will define variables for the plugin in the vars.js file"""
        vars_js = self.get_vars_js()
        if vars_js:
            return 'var {}Plugin = {};'.format(self.name.title(), json.dumps(vars_js))

    def template_hook(self, name, receiver, priority=50, markup=True):
        """Registers a function to be called when a template hook is invoked.

        The receiver function should always support arbitrary ``**kwargs``
        to prevent breakage in future Indico versions which might add new
        arguments to a hook::

            def receiver(something, **kwargs):
                return do_stuff(something)

        It needs to return a unicode string. If you intend to return plaintext
        it is adviable to set the `markup` param to `False` which results in the
        string being considered "unsafe" which will cause it to be HTML-escaped.

        :param name: The name of the template hook.
        :param receiver: The receiver function.
        :param priority: The priority to use when multiple plugins
                         inject data for the same hook.
        :param markup: If the returned data is HTML
        """
        self.connect(signals.plugin.template_hook, lambda _, **kw: (markup, priority, receiver(**kw)),
                     sender=unicode(name))

    @classproperty
    @classmethod
    def instance(cls):
        """The Plugin instance used by the current app"""
        instance = plugin_engine.get_plugin(cls.name)
        if instance is None:
            raise RuntimeError('Plugin is not active in the current app')
        return instance

    @classproperty
    @classmethod
    def logger(cls):
        return Logger.get('plugin.{}'.format(cls.name))

    @cached_classproperty
    @classmethod
    def settings(cls):
        """:class:`SettingsProxy` for the plugin's settings"""
        if cls.name is None:
            raise RuntimeError('Plugin has not been loaded yet')
        instance = cls.instance
        with instance.plugin_context():  # in case the default settings come from a property
            return SettingsProxy('plugin_{}'.format(cls.name), instance.default_settings, cls.strict_settings)

    @cached_classproperty
    @classmethod
    def event_settings(cls):
        """:class:`EventSettingsProxy` for the plugin's event-specific settings"""
        if cls.name is None:
            raise RuntimeError('Plugin has not been loaded yet')
        instance = cls.instance
        with instance.plugin_context():  # in case the default settings come from a property
            return EventSettingsProxy('plugin_{}'.format(cls.name), instance.default_event_settings,
                                      cls.strict_settings)


def include_plugin_js_assets(bundle_name):
    """Jinja template function to generate HTML tags for a plugin JS asset bundle."""
    return Markup('\n'.join('<script src="{}"></script>'.format(url)
                            for url in current_plugin.assets[bundle_name].urls()))


def include_plugin_css_assets(bundle_name):
    """Jinja template function to generate HTML tags for a plugin CSS asset bundle."""
    return Markup('\n'.join('<link rel="stylesheet" type="text/css" href="{}">'.format(url)
                            for url in current_plugin.assets[bundle_name].urls()))


def plugin_hook(*name, **kwargs):
    """Template function to let plugins add their own data to a template.

    :param name: The name of the hook.  Only accepts one argument.
    :param kwargs: Data to pass to the signal receivers.
    """
    if len(name) != 1:
        raise TypeError('plugin_hook() accepts only one positional argument, {} given'.format(len(name)))
    name = name[0]
    values = []
    for is_markup, priority, value in values_from_signal(signals.plugin.template_hook.send(unicode(name), **kwargs),
                                                         single_value=True):
        if value:
            if is_markup:
                value = Markup(value)
            heappush(values, (priority, value))
    return Markup(u'\n').join(x[1] for x in values) if values else ''


def plugin_url_rule_to_js(endpoint):
    """Like :func:`~indico.web.flask.util.url_rule_to_js` but prepending plugin name prefix to the endpoint"""
    if '.' in endpoint[1:]:  # 'foo' or '.foo' should not get the prefix
        endpoint = 'plugin_{}'.format(endpoint)
    return url_rule_to_js(endpoint)


def url_for_plugin(endpoint, *targets, **values):
    """Like :func:`~indico.web.flask.util.url_for` but prepending ``'plugin_'`` to the blueprint name."""
    if '.' in endpoint[1:]:  # 'foo' or '.foo' should not get the prefix
        endpoint = 'plugin_{}'.format(endpoint)
    return url_for(endpoint, *targets, **values)


def get_plugin_template_module(template_name, **context):
    """Like :func:`~indico.web.flask.templating.get_template_module`, but using plugin templates"""
    template_name = '{}:{}'.format(current_plugin.name, template_name)
    return get_template_module(template_name, **context)


def wrap_cli_manager(manager, plugin):
    """Wraps all commands of a flask-script `Manager` in a plugin context.

    This actually clones the manager, so the original one is left untouched.
    """
    manager = deepcopy(manager)
    for name, command in manager._commands.iteritems():
        command = deepcopy(command)
        command.run = wrap_in_plugin_context(plugin, command.run)
        manager._commands[name] = command
    return manager


class IndicoPluginEngine(PluginEngine):
    plugin_class = IndicoPlugin


class IndicoPluginBlueprintSetupState(PluginBlueprintSetupStateMixin, IndicoBlueprintSetupState):
    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        if rule.startswith('/static'):
            with self._unprefixed():
                super(IndicoPluginBlueprintSetupState, self).add_url_rule(rule, endpoint, view_func, **options)
        else:
            super(IndicoPluginBlueprintSetupState, self).add_url_rule(rule, endpoint, view_func, **options)


class IndicoPluginBlueprint(PluginBlueprintMixin, IndicoBlueprint):
    """The Blueprint class all plugins need to use.

    It contains the necessary logic to run the blueprint's view
    functions inside the correct plugin context and to make the
    static folder work.
    """
    def make_setup_state(self, app, options, first_registration=False):
        return IndicoPluginBlueprintSetupState(self, app, options, first_registration)


class WPJinjaMixinPlugin(WPJinjaMixin):
    render_template_func = staticmethod(render_plugin_template)


plugin_engine = IndicoPluginEngine()

# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import errno
import json
import os

from flask import g, session
from flask_babelex import Domain
from flask_pluginengine import (Plugin, PluginBlueprintMixin, PluginBlueprintSetupStateMixin, PluginEngine,
                                current_plugin, render_plugin_template, wrap_in_plugin_context)
from werkzeug.utils import cached_property

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import import_all_models
from indico.core.logger import Logger
from indico.core.settings import SettingsProxy
from indico.core.webpack import IndicoManifestLoader
from indico.modules.events.settings import EventSettingsProxy
from indico.modules.events.static.util import RewrittenManifest
from indico.modules.users import UserSettingsProxy
from indico.util.decorators import cached_classproperty, classproperty
from indico.util.i18n import NullDomain, _
from indico.util.struct.enum import IndicoEnum
from indico.web.flask.templating import get_template_module, register_template_hook
from indico.web.flask.util import url_for, url_rule_to_js
from indico.web.flask.wrappers import IndicoBlueprint, IndicoBlueprintSetupState
from indico.web.menu import SideMenuItem
from indico.web.views import WPJinjaMixin


class PluginCategory(unicode, IndicoEnum):
    search = _('Search')
    synchronization = _('Synchronization')
    payment = _('Payment')
    importers = _('Importers')
    videoconference = _('Videoconference')
    other = _('Other')


class IndicoPlugin(Plugin):
    """Base class for an Indico plugin.

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
    #: A dictionary containing default values for user-specific settings
    default_user_settings = {}
    #: A set containing the names of settings which store ACLs
    acl_settings = frozenset()
    #: A set containing the names of event-specific settings which store ACLs
    acl_event_settings = frozenset()
    #: A dict containing custom converters for settings
    settings_converters = {}
    #: A dict containing custom converters for event-specific settings
    event_settings_converters = {}
    #: A dict containing custom converters for user-specific settings
    user_settings_converters = {}
    #: If the plugin should link to a details/config page in the admin interface
    configurable = False
    #: The group category that the plugin belongs to
    category = None
    #: If `settings`, `event_settings` and `user_settings` should use strict
    #: mode, i.e. only allow keys in `default_settings`, `default_event_settings`
    #: or `default_user_settings` (or the related `acl_settings` sets).
    #: This should not be disabled in most cases; if you need to store arbitrary
    #: keys, consider storing a dict inside a single top-level setting.
    strict_settings = True

    def init(self):
        """Called when the plugin is being loaded/initialized.

        If you want to run custom initialization code, this is the
        method to override. Make sure to call the base method or
        the other overridable methods in this class will not be
        called anymore.
        """
        assert self.configurable or not self.settings_form, 'Non-configurable plugin cannot have a settings form'
        self.alembic_versions_path = os.path.join(self.root_path, 'migrations')
        self.connect(signals.plugin.get_blueprints, lambda app: self.get_blueprints())
        self.template_hook('vars-js', self.inject_vars_js)
        self._import_models()

    def _import_models(self):
        old_models = set(db.Model._decl_class_registry.items())
        import_all_models(self.package_name)
        added_models = set(db.Model._decl_class_registry.items()) - old_models
        # Ensure that only plugin schemas have been touched. It would be nice if we could actually
        # restrict a plugin to plugin_PLUGNNAME but since we load all models from the plugin's package
        # which could contain more than one plugin this is not easily possible.
        for name, model in added_models:
            schema = model.__table__.schema
            # Allow models with non-plugin schema if they specify `polymorphic_identity` without a dedicated table
            if ('polymorphic_identity' in getattr(model, '__mapper_args__', ())
                    and '__tablename__' not in model.__dict__):
                continue
            if not schema.startswith('plugin_'):
                raise Exception("Plugin '{}' added a model which is not in a plugin schema ('{}' in '{}')"
                                .format(self.name, name, schema))

    def connect(self, signal, receiver, **connect_kwargs):
        connect_kwargs['weak'] = False
        func = wrap_in_plugin_context(self, receiver)
        func.indico_plugin = self
        signal.connect(func, **connect_kwargs)

    def get_blueprints(self):
        """Return blueprints to be registered on the application.

        A single blueprint can be returned directly, for multiple blueprint you need
        to yield them or return an iterable.
        """
        pass

    def get_vars_js(self):
        """Return a dictionary with variables to be added to vars.js file."""
        return None

    @cached_property
    def translation_path(self):
        """Return translation files to be used by the plugin.

        By default, get <root_path>/translations, unless it does not exist.
        """
        translations_path = os.path.join(self.root_path, 'translations')
        return translations_path if os.path.exists(translations_path) else None

    @cached_property
    def translation_domain(self):
        """Return the domain for this plugin's translation_path."""
        path = self.translation_path
        return Domain(path) if path else NullDomain()

    def _get_manifest(self):
        try:
            loader = IndicoManifestLoader(custom=False)
            return loader.load(os.path.join(self.root_path, 'static', 'dist', 'manifest.json'))
        except IOError as exc:
            if exc.errno != errno.ENOENT:
                raise
            return None

    @property
    def manifest(self):
        if g.get('static_site') and 'custom_manifests' in g:
            try:
                return g.custom_manifests[self.name]
            except KeyError:
                manifest = self._get_manifest()
                g.custom_manifests[self.name] = RewrittenManifest(manifest) if manifest else None
                return g.custom_manifests[self.name]
        return self._get_manifest()

    def inject_bundle(self, name, view_class=None, subclasses=True, condition=None):
        """Inject an asset bundle into Indico's pages.

        :param name: Name of the bundle
        :param view_class: If a WP class is specified, only inject it into pages using that class
        :param subclasses: also inject into subclasses of `view_class`
        :param condition: a callable to determine whether to inject or not. only called, when the
                          view_class criterion matches
        """

        def _do_inject(sender):
            if condition is None or condition():
                return self.manifest[name]

        if view_class is None:
            self.connect(signals.plugin.inject_bundle, _do_inject)
        elif not subclasses:
            self.connect(signals.plugin.inject_bundle, _do_inject, sender=view_class)
        else:
            def _func(sender):
                if issubclass(sender, view_class):
                    return _do_inject(sender)

            self.connect(signals.plugin.inject_bundle, _func)

    def inject_vars_js(self):
        """
        Return a string that will define variables for the plugin in
        the vars.js file.
        """
        vars_js = self.get_vars_js()
        if vars_js:
            return 'var {}Plugin = {};'.format(self.name.title(), json.dumps(vars_js))

    def template_hook(self, name, receiver, priority=50, markup=True):
        """Register a function to be called when a template hook is invoked.

        For details see :func:`~indico.web.flask.templating.register_template_hook`.
        """
        register_template_hook(name, receiver, priority, markup, self)

    @classproperty
    @classmethod
    def logger(cls):
        return Logger.get('plugin.{}'.format(cls.name))

    @cached_classproperty
    @classmethod
    def settings(cls):
        """:class:`SettingsProxy` for the plugin's settings."""
        if cls.name is None:
            raise RuntimeError('Plugin has not been loaded yet')
        instance = cls.instance
        with instance.plugin_context():  # in case the default settings come from a property
            return SettingsProxy('plugin_{}'.format(cls.name), instance.default_settings, cls.strict_settings,
                                 acls=cls.acl_settings, converters=cls.settings_converters)

    @cached_classproperty
    @classmethod
    def event_settings(cls):
        """:class:`EventSettingsProxy` for the plugin's event-specific settings."""
        if cls.name is None:
            raise RuntimeError('Plugin has not been loaded yet')
        instance = cls.instance
        with instance.plugin_context():  # in case the default settings come from a property
            return EventSettingsProxy('plugin_{}'.format(cls.name), instance.default_event_settings,
                                      cls.strict_settings, acls=cls.acl_event_settings,
                                      converters=cls.event_settings_converters)

    @cached_classproperty
    @classmethod
    def user_settings(cls):
        """:class:`UserSettingsProxy` for the plugin's user-specific settings."""
        if cls.name is None:
            raise RuntimeError('Plugin has not been loaded yet')
        instance = cls.instance
        with instance.plugin_context():  # in case the default settings come from a property
            return UserSettingsProxy('plugin_{}'.format(cls.name), instance.default_user_settings,
                                     cls.strict_settings, converters=cls.user_settings_converters)


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
    # This is the same value as in WPJinjaMixin but NOT redundant:
    # A plugin may have a WP inheriting from `WPJinjaMixinPlugin, WPSomethingElse`
    # to get the render_template_func from here while `WPSomethingElse`
    # already sets a template prefix and also inherits from WPJinjaMixin,
    # in which case the WPJinjaMixin from here would be skipped due to how
    # Python's MRO works and thus the template prefix would not be cleared.
    template_prefix = ''


@signals.menu.items.connect_via('admin-sidemenu')
def _extend_admin_menu(sender, **kwargs):
    if session.user.is_admin:
        return SideMenuItem('plugins', _('Plugins'), url_for('plugins.index'), 80, icon='puzzle')


plugin_engine = IndicoPluginEngine()

# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import itertools
import posixpath
import re
import typing as t
from dataclasses import dataclass
from types import GeneratorType

from dateutil.relativedelta import relativedelta
from flask import current_app
from flask_pluginengine.templating import PluginEnvironment
from flask_pluginengine.util import get_state
from jinja2 import environmentfilter
from jinja2.filters import _GroupTuple, make_attrgetter
from jinja2.loaders import BaseLoader, FileSystemLoader, TemplateNotFound, split_template_path
from jinja2.runtime import StrictUndefined
from jinja2.utils import internalcode
from markupsafe import Markup

from indico.core import signals
from indico.util.signals import values_from_signal
from indico.util.string import natural_sort_key, render_markdown


indentation_re = re.compile(r'^ +', re.MULTILINE)


def underline(s, sep='-'):
    return f'{s}\n{sep * len(s)}'


def markdown(value):
    return Markup(render_markdown(value, extensions=('nl2br', 'tables')))


def dedent(value):
    """Remove leading whitespace from each line."""
    return indentation_re.sub('', value)


@environmentfilter
def natsort(environment, value, reverse=False, case_sensitive=False, attribute=None):
    """Sort an iterable in natural order.

    Per default it sorts ascending,
    if you pass it true as first argument it will reverse the sorting.

    If the iterable is made of strings the third parameter can be used to
    control the case sensitiveness of the comparison which is disabled by
    default.

    Based on Jinja2's `sort` filter.
    """
    if not case_sensitive:
        def sort_func(item):
            if isinstance(item, str):
                item = item.lower()
            return natural_sort_key(item)
    else:
        sort_func = natural_sort_key

    if attribute is not None:
        getter = make_attrgetter(environment, attribute)

        def sort_func(item, processor=sort_func or (lambda x: x)):
            return processor(getter(item))

    return sorted(value, key=sort_func, reverse=reverse)


@environmentfilter
def groupby(environment, value, attribute, reverse=False):
    """Like Jinja's builtin `groupby` filter, but allows reversed order."""
    expr = make_attrgetter(environment, attribute)
    return [_GroupTuple(key, list(values))
            for key, values in itertools.groupby(sorted(value, key=expr, reverse=reverse), expr)]


def plusdelta(value, **kwargs):
    """Add a relativedelta to a datetime object."""
    return value + relativedelta(**kwargs)


def decodeprincipal(value, **kwargs):
    """Decode a principal into an actual object."""
    from indico.util.user import principal_from_identifier
    return principal_from_identifier(value, soft_fail=True, **kwargs)


def instanceof(value, type_):
    """Check if `value` is an instance of `type_`.

    :param value: an object
    :param type_: a type
    """
    return isinstance(value, type_)


def subclassof(value, type_):
    """Check if `value` is a subclass of `type_`.

    :param value: a type
    :param type_: a type
    """
    return issubclass(value, type_)


def get_overridable_template_name(name, plugin, core_prefix='', plugin_prefix=''):
    """Return template names for templates that may be overridden in a plugin.

    :param name: the name of the template
    :param plugin: the :class:`IndicoPlugin` that may override it (can be none)
    :param core_prefix: the path prefix of the template in the core
    :param plugin_prefix: the path prefix of the template in the plugin
    :return: template name or list of template names
    """
    core_tpl = core_prefix + name
    if plugin is None:
        return core_tpl
    else:
        return [f'{plugin.name}:{plugin_prefix}{name}', core_tpl]


def get_template_module(template_name_or_list, **context):
    """Return the python module of a template.

    This allows you to call e.g. macros inside it from Python code."""
    current_app.update_template_context(context)
    tpl = current_app.jinja_env.get_or_select_template(template_name_or_list)
    return tpl.make_module(context)


@dataclass(frozen=True)
class TemplateSnippet:
    """A snippet to be returned by a template hook.

    The `content` is typically string or Markup object, but in some special cases
    it may also be a different object.

    Typically this class does not need to be used when registering a template hook
    unless you need the ability to specify priority or disable markup wrapping at
    execution time, or yield multiple snippets with different settings.
    """

    content: t.Any
    markup: bool = True
    priority: int = 50


def register_template_hook(name, receiver, priority=50, markup=True, plugin=None):
    """Register a function to be called when a template hook is invoked.

    The receiver function should always support arbitrary ``**kwargs``
    to prevent breakage in future Indico versions which might add new
    arguments to a hook::

        def receiver(something, **kwargs):
            return do_stuff(something)

    It needs to return a unicode string. If you intend to return plaintext
    it is advisable to set the `markup` param to `False` which results in the
    string being considered "unsafe" which will cause it to be HTML-escaped.

    :param name: The name of the template hook.
    :param receiver: The receiver function.
    :param priority: The priority to use when multiple plugins
                     inject data for the same hook.
    :param markup: If the returned data is HTML
    """
    def _func(_, **kw):
        res = receiver(**kw)
        res = tuple(res) if isinstance(res, GeneratorType) else (res,)
        return tuple(x if isinstance(x, TemplateSnippet) else TemplateSnippet(x, markup, priority) for x in res)

    if plugin is None:
        signals.plugin.template_hook.connect(_func, sender=str(name), weak=False)
    else:
        plugin.connect(signals.plugin.template_hook, _func, sender=str(name))


def template_hook(name, priority=50, markup=True):
    """Decorator for register_template_hook."""
    def decorator(func):
        register_template_hook(name, func, priority, markup)
        return func

    return decorator


def call_template_hook(*name, **kwargs):
    """Template function to let plugins add their own data to a template.

    :param name: The name of the hook.  Only accepts one argument.
    :param as_list: Return a list instead of a concatenated string
    :param kwargs: Data to pass to the signal receivers.
    """
    if len(name) != 1:
        raise TypeError(f'call_template_hook() accepts only one positional argument, {len(name)} given')
    name = name[0]
    as_list = kwargs.pop('as_list', False)
    values = []
    for snippet in values_from_signal(signals.plugin.template_hook.send(str(name), **kwargs),
                                      multi_value_types=tuple, as_list=True):
        if not (value := snippet.content):
            continue
        if snippet.markup:
            value = Markup(value)
        values.append((snippet.priority, value))
    values.sort()
    if as_list:
        return [x[1] for x in values]
    else:
        return Markup('\n').join(x[1] for x in values) if values else ''


class CustomizationLoader(BaseLoader):
    def __init__(self, fallback_loader, customization_dir, customization_debug=False):
        from indico.core.logger import Logger
        self.logger = Logger.get('customization')
        self.debug = customization_debug
        self.fallback_loader = fallback_loader
        self.fs_loader = FileSystemLoader(customization_dir, followlinks=True)

    def _get_fallback(self, environment, template, path, customization_ignored=False):
        rv = self.fallback_loader.get_source(environment, template)
        if not customization_ignored and self.debug:
            try:
                orig_path = rv[1]
            except TemplateNotFound:
                orig_path = None
            self.logger.debug('Customizable: %s (original: %s, reference: ~%s)', path, orig_path, template)
        return rv

    def get_source(self, environment, template):
        path = posixpath.join(*split_template_path(template))
        if template[0] == '~':
            return self._get_fallback(environment, template[1:], path[1:], customization_ignored=True)
        try:
            plugin, path = path.split(':', 1)
        except ValueError:
            plugin = None
        prefix = posixpath.join('plugins', plugin) if plugin else 'core'
        path = posixpath.join(prefix, path)
        try:
            rv = self.fs_loader.get_source(environment, path)
            if self.debug:
                self.logger.debug('Customized: %s', path)
            return rv
        except TemplateNotFound:
            return self._get_fallback(environment, template, path)

    @internalcode
    def load(self, environment, name, globals=None):
        tpl = super().load(environment, name, globals)
        if ':' not in name:
            return tpl
        # This is almost exactly what PluginPrefixLoader.load() does, but we have
        # to replicate it here since we need to handle `~` and use our custom
        # `get_source` to get the overridden template
        plugin_name, tpl_name = name.split(':', 1)
        if plugin_name[0] == '~':
            plugin_name = plugin_name[1:]
        plugin = get_state(current_app).plugin_engine.get_plugin(plugin_name)
        if plugin is None:
            # that should never happen
            raise RuntimeError(f'Plugin template {name} has no plugin')
        tpl.plugin = plugin
        return tpl


def _convert_undefined(new_cls, undefined):
    return new_cls(
        hint=undefined._undefined_hint,
        obj=undefined._undefined_obj,
        name=undefined._undefined_name,
        exc=undefined._undefined_exception,
    )


class SemiStrictUndefined(StrictUndefined):
    """Like `StrictUndefined` but allows truthiness checks.

    This allows for code such as ``{% if foo.bar %}`` and comparisons which are
    widely used and thus raising exceptions would be somewhat annoying. And unlike
    undefined top-level variables undefined attributes/items are much more likely
    to show up when testing things.
    """

    def __bool__(self):
        return False

    def __eq__(self, other):
        return type(self) is type(other)

    def __ne__(self, other):
        return not self.__eq__(other)


class IndicoEnvironment(PluginEnvironment):
    def getattr(self, obj, attribute):
        rv = super().getattr(obj, attribute)
        if isinstance(rv, StrictUndefined):
            # we only care about top-level undefineds, so if getting an attribute returns
            # undefined, we switch to a less strict Undefined implementation
            return _convert_undefined(SemiStrictUndefined, rv)
        return rv

    def getitem(self, obj, argument):
        rv = super().getitem(obj, argument)
        if isinstance(rv, StrictUndefined):
            # we only care about top-level undefineds, so if getting an item returns
            # undefined, we switch to a less strict Undefined implementation
            return _convert_undefined(SemiStrictUndefined, rv)
        return rv

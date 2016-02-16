# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from collections import OrderedDict

from flask import request, render_template
from flask_pluginengine import plugin_context
from indico.util.decorators import cached_classproperty

from indico.core import signals
from indico.util.caching import memoize_request
from indico.util.signals import values_from_signal, named_objects_from_signal


class EventCloner(object):
    """
    Base class to define cloning operations to be executed when an
    event is cloned.

    :param old_event: The event that's being cloned
    """

    #: unique name of the clone action
    name = None
    #: the displayed name of the cloner
    friendly_name = None
    #: cloners that must be selected for this one to be available.
    #: they are also guaranteed to run before this one.
    requires = frozenset()
    #: cloners that must run before this one (if enabled), but this
    #: one runs even if they are not enabled
    uses = frozenset()
    #: Whether the clone operation is selected by default.
    #: Use this to deselect options which are less common and thus
    #: should not be enabled by default when cloning an event.
    is_default = False
    #: Whether this cloner is internal and never shown in the list.
    #: An internal cloner is executed when `is_default` is set to
    #: ``True`` or another cloner depends on it (always use `requires`
    #: for this; `uses` will not enable an internal cloner).  If
    #: you override `is_visible` for an internal cloner (which only
    #: makes sense when turning `is_internal` into a property), make
    #: sure to check the super return value of `is_visible` to prevent
    #: an internal cloner from showing up in the cloner selection.
    is_internal = False

    @classmethod
    def get_form_items(cls, old_event):
        cloners = sorted([cloner_cls(old_event) for cloner_cls in get_event_cloners().itervalues()],
                         key=lambda x: x.friendly_name)
        return render_template('events/cloner_options.html', cloners=cloners)

    @classmethod
    def run_cloners(cls, old_event, new_event):
        selected = {x[7:] for x in request.values.getlist('cloners') if x.startswith('cloner_')}
        all_cloners = OrderedDict((name, cloner_cls(old_event))
                                  for name, cloner_cls in get_event_cloners().iteritems())
        if any(cloner.is_internal for name, cloner in all_cloners.iteritems() if name in selected):
            raise Exception('An internal cloner was selected')
        # enable internal cloners that are enabled by default or required by another cloner
        selected |= {c.name
                     for c in all_cloners.itervalues()
                     if c.is_internal and (c.is_default or c.required_by_deep & selected)}
        active_cloners = OrderedDict((name, cloner) for name, cloner in all_cloners.iteritems() if name in selected)
        if not all((c.is_internal or c.is_visible) and c.is_available for c in active_cloners.itervalues()):
            raise Exception('An invisible/unavailable cloner was selected')
        for name, cloner in active_cloners.iteritems():
            if not (selected >= cloner.requires_deep):
                raise Exception('Cloner {} requires {}'.format(name, ', '.join(cloner.requires_deep - selected)))
        shared_data = {}
        cloner_names = set(active_cloners)
        for name, cloner in active_cloners.iteritems():
            shared_data[name] = cloner.run(new_event, cloner_names, cloner._prepare_shared_data(shared_data))

    @cached_classproperty
    @classmethod
    def requires_deep(cls):
        """All cloner names required by this cloner.

        This includes cloners required by a requirement.
        """
        cloners = get_event_cloners()
        todo = set(cls.requires)
        required = set()
        while todo:
            cloner = todo.pop()
            required.add(cloner)
            todo |= cloners[cloner].requires
        return required

    @cached_classproperty
    @classmethod
    def required_by_deep(cls):
        """All cloner names depending on this cloner.

        This includes cloners which depend on a cloner depending on
        this cloner.
        """
        # This is not very efficient, but it runs exactly once on a not-very-large set
        return {cloner.name for cloner in get_event_cloners().itervalues() if cls.name in cloner.requires_deep}

    def __init__(self, old_event):
        self.old_event = old_event

    def run(self, new_event, cloners, shared_data):
        """Performs the cloning operation.

        :param new_event: The `Event` that's created by the cloning
                          operation.
        :param cloners: A set containing the names of all enabled
                        cloners.
        :param shared_data: A dict containing the data returned by
                            other cloners.  Only data from cloners
                            specified in `requires` or `uses` will
                            be available in the dict.  If a *used*
                            cloner was not selected, its name will
                            not be present in the data dict.  The
                            value may be ``None`` depending on the
                            cloner. This would indicate that the
                            cloner was executed but did not return
                            any data.
        :return: data that may be used by other cloners depending on
                 or using this cloner
        """
        raise NotImplementedError

    @property
    def is_visible(self):
        """Whether the clone operation should be shown at all.

        Use this to hide an option because of a feature not being
        enabled or because of the event type not supporting it.
        """
        return not self.is_internal

    @property
    def is_available(self):
        """Whether the clone operation can be selected.

        Use this to disable options if selecting them wouldn't make
        sense, e.g. because there is nothing to clone.
        """
        return True

    def _prepare_shared_data(self, shared_data):
        linked = self.uses | self.requires
        return {k: v for k, v in shared_data.iteritems() if k in linked}


def _resolve_dependencies(cloners):
    cloner_deps = {name: (cls.requires, cls.uses) for name, cls in cloners.iteritems()}
    resolved_deps = set()
    while cloner_deps:
        # Get cloners with both hard and soft dependencies being met
        ready = {cls for cls, deps in cloner_deps.iteritems() if all(d <= resolved_deps for d in deps)}
        if not ready:
            # Otherwise check for cloners with all hard dependencies being met
            ready = {cls for cls, deps in cloner_deps.iteritems() if deps[0] <= resolved_deps}
        if not ready:
            # Either a circular dependency or a dependency that's not loaded
            raise Exception('Could not resolve dependencies between cloners (remaining: {})'
                            .format(', '.join(cloner_deps)))
        resolved_deps |= ready
        for name in ready:
            yield name, cloners[name]
            del cloner_deps[name]


@memoize_request
def get_event_cloners():
    """Get the dict containing all available event cloners.

    The returned dict is ordered based on the dependencies of each
    cloner and when executing the cloners MUST be executed in that
    order.
    """
    cloners = named_objects_from_signal(signals.event_management.get_cloners.send(), plugin_attr='plugin')
    return OrderedDict(_resolve_dependencies(cloners))


class LegacyEventCloner(object):
    """Base class to let plugins/modules plug into the event cloning mechanism"""

    @staticmethod
    def get_plugin_items(conf):
        """Returns the items/checkboxes for the clone options provided by EventCloner"""
        plugin_options = []
        for plugin_cloner in values_from_signal(signals.event_management.clone.send(conf), single_value=True):
            with plugin_context(plugin_cloner.plugin):
                for name, (title, enabled, checked) in plugin_cloner.get_options().iteritems():
                    full_name = plugin_cloner.full_option_name(name)
                    plugin_options.append((
                        title,
                        """<li><input type="checkbox" name="cloners" id="cloner-{0}" value="{0}" {2} {3}>{1}</li>"""
                        .format(full_name, title,
                                'disabled' if not enabled else '',
                                'checked' if checked and enabled else '')
                        .encode('utf-8')
                    ))
        return '\n'.join(x[1] for x in sorted(plugin_options))

    @staticmethod
    def clone_event(old_conf, new_conf):
        """Calls the various cloning methods"""
        selected = set(request.values.getlist('cloners'))
        for plugin_cloner in values_from_signal(signals.event_management.clone.send(old_conf), single_value=True):
            with plugin_context(plugin_cloner.plugin):
                selected_options = {name for name, (_, enabled, _) in plugin_cloner.get_options().iteritems()
                                    if enabled and plugin_cloner.full_option_name(name) in selected}
                plugin_cloner.clone(new_conf, selected_options)

    def __init__(self, conf, plugin=None):
        self.event = conf
        self.plugin = plugin

    def full_option_name(self, option):
        return '{}-{}'.format(self.__module__, option)

    def get_options(self):
        """Returns a dict containing the clone options.

        :return: dict mapping option names to ``title, enabled, checked`` tuples
        """
        raise NotImplementedError

    def clone(self, new_conf, options):
        """Performs the actual cloning.

        This method is always called, even if no options are selected!

        :param new_conf: The new event created during the clone
        :param options: A set containing the options provided by
                        this class which the user has selected
        """
        raise NotImplementedError

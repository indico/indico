# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from collections import OrderedDict
from operator import attrgetter

from indico.core import signals
from indico.util.caching import memoize_request
from indico.util.decorators import cached_classproperty
from indico.util.signals import named_objects_from_signal


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
    #: Whether this cloner is always available when pulled in as a
    #: 'requires' dependency.  This allows requiring a cloner without
    #: having to keep it available even if there are no clonable
    #: objects.  For example, you may have something that uses the
    #: 'tracks' cloner since it can reference tracks (and thus needs
    #: them cloned) but also contains various other things that may
    #: be clone-worthy even without tracks being set-up.  While one
    #: may think about using 'uses' instead of 'requires' first this
    #: would result in people having to explicitly enable the other
    #: cloner even if it makes no sense to not run it.
    always_available_dep = False
    #: Whether this cloner only allows cloning into new events and
    #: is not available when importing into an existing event.
    new_event_only = False

    @classmethod
    def get_cloners(cls, old_event):
        """Return the list of cloners (sorted for display)."""
        return sorted((cloner_cls(old_event) for cloner_cls in get_event_cloners().itervalues()),
                      key=attrgetter('friendly_name'))

    @classmethod
    def run_cloners(cls, old_event, new_event, cloners, n_occurrence=0, event_exists=False):
        all_cloners = OrderedDict((name, cloner_cls(old_event, n_occurrence))
                                  for name, cloner_cls in get_event_cloners().iteritems())
        if any(cloner.is_internal for name, cloner in all_cloners.iteritems() if name in cloners):
            raise Exception('An internal cloner was selected')

        if event_exists:
            if any(cloner.new_event_only for name, cloner in all_cloners.viewitems() if name in cloners):
                raise Exception('A new event only cloner was selected')
            if any(cloner.has_conflicts(new_event) for name, cloner in all_cloners.viewitems() if name in cloners):
                raise Exception('Cloner target is not empty')

        # enable internal cloners that are enabled by default or required by another cloner
        cloners |= {c.name
                    for c in all_cloners.itervalues()
                    if c.is_internal and (c.is_default or c.required_by_deep & cloners)}
        # enable unavailable cloners that may be pulled in as a dependency nonetheless
        extra = {c.name
                 for c in all_cloners.itervalues()
                 if not c.is_available and c.always_available_dep and c.required_by_deep & cloners}
        cloners |= extra
        active_cloners = OrderedDict((name, cloner) for name, cloner in all_cloners.iteritems() if name in cloners)
        if not all((c.is_internal or c.is_visible) and c.is_available
                   for c in active_cloners.itervalues()
                   if c.name not in extra):
            raise Exception('An invisible/unavailable cloner was selected')
        for name, cloner in active_cloners.iteritems():
            if not (cloners >= cloner.requires_deep):
                raise Exception('Cloner {} requires {}'.format(name, ', '.join(cloner.requires_deep - cloners)))
        shared_data = {}
        cloner_names = set(active_cloners)
        for name, cloner in active_cloners.iteritems():
            shared_data[name] = cloner.run(new_event, cloner_names, cloner._prepare_shared_data(shared_data),
                                           event_exists=event_exists)

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

    def __init__(self, old_event, n_occurrence=0):
        self.old_event = old_event
        self.n_occurrence = n_occurrence

    def run(self, new_event, cloners, shared_data, event_exists=False):
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
        :param event_exists: If cloning into an existing event
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

    def has_conflicts(self, target_event):
        """Check for conflicts between source event and target event.

        Use this when cloning into an existing event to disable options
        where ``target_event`` data would conflict with cloned data.
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

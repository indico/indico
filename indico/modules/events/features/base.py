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

from indico.modules.events.features.util import get_feature_definitions
from indico.util.decorators import cached_classproperty


class EventFeature(object):
    """Base class for event features.

    To create a new feature, subclass this class and register
    it using the `event.get_feature_definitions` signal.
    Feature classes are never instatiated.

    You have multiple ways of requiring a feature to be enabled:

    If you simply want to run some code if a feature is (not) enabled,
    use ``event.has_feature('feature')`` to check it.  This is
    especially useful in signal handlers, but make sure you only check
    the feature for signals where it makes sense.  For example, you
    probably want to handle ``event.deleted`` no matter if the feature
    is enabled or not (as it might have been enabled before).

    If a blueprint has no endpoints that need to work without the
    feature enabled, set the ``event_feature`` kwarg of
    `IndicoBlueprint` to the name of your feature.  This will make any
    request to that blueprint fail with an error unless the feature is
    enabled.

    If you only want to certain RHs to require a feature, you can set
    their ``EVENT_FEATURE`` class attribute to the name of your feature.
    The behavior in case of a disabled feature is the same as for
    blueprint-level features.
    """

    #: unique name of the feature
    name = None
    #: plugin containing this feature - assigned automatically
    plugin = None
    #: displayed name of the feature (shown to users)
    friendly_name = None
    #: description of the feature (optional)
    description = None
    #: the names of features which must be enabled before this feature
    #: may be enabled
    requires = frozenset()

    @classmethod
    def is_default_for_event(cls, event):  # pragma: no cover
        """Checks if the feature should be enabled by default"""
        return False

    @classmethod
    def is_allowed_for_event(cls, event):  # pragma: no cover
        """Check if the feature can be enabled in an event"""
        return True

    @classmethod
    def enabled(cls, event):  # pragma: no cover
        """Called when the feature is enabled for an event"""
        pass

    @classmethod
    def disabled(cls, event):  # pragma: no cover
        """Called when the feature is disabled for an event"""
        pass

    @cached_classproperty
    @classmethod
    def requires_deep(cls):
        """All feature names required by this feature.

        This includes features required by a requirement.
        """
        feature_definitions = get_feature_definitions()
        todo = set(cls.requires)
        features = set()
        while todo:
            feature = todo.pop()
            features.add(feature)
            todo |= feature_definitions[feature].requires
        return features

    @cached_classproperty
    @classmethod
    def required_by_deep(cls):
        """All feature names depending on this feature.

        This includes features which depend on a feature depending on
        this feature.
        """
        # This is not very efficient, but it runs exactly one on a not-very-large set
        return {feature.name for feature in get_feature_definitions().itervalues() if cls.name in feature.requires_deep}

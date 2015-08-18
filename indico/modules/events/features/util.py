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

from __future__ import unicode_literals

from werkzeug.exceptions import NotFound

from indico.core import signals
from indico.core.db import db, DBMgr
from indico.modules.events.features import event_settings as features_event_settings
from indico.util.signals import named_objects_from_signal


def get_feature_definitions():
    """Gets a dict containing all feature definitions"""
    return named_objects_from_signal(signals.event.get_feature_definitions.send(), plugin_attr='plugin')


def get_feature_definition(name):
    """Gets a feature definition"""
    try:
        return get_feature_definitions()[name]
    except KeyError:
        raise RuntimeError('Feature does not exist: {}'.format(name))


def get_enabled_features(event):
    """Returns a set of enabled feature names for an event"""
    enabled_features = features_event_settings.get(event, 'enabled')
    if enabled_features is not None:
        return set(enabled_features)
    else:
        return {name for name, feature in get_feature_definitions().iteritems() if feature.is_default_for_event(event)}


def set_feature_enabled(event, name, state):
    """Enables/disables a feature for an event

    :param event: The event.
    :param name: The name of the feature.
    :param state: If the feature is enabled or not.
    :return: Boolean indicating if the state of the feature changed.
    """
    feature = get_feature_definition(name)
    enabled = get_enabled_features(event)
    if (name in enabled) == state:
        return False
    if state:
        enabled.add(name)
        func = feature.enabled
    else:
        enabled.discard(name)
        func = feature.disabled
    features_event_settings.set(event, 'enabled', sorted(enabled))
    db.session.flush()
    func(event)
    return True


def is_feature_enabled(event, name):
    """Checks if a feature is enabled for an event.

    :param event: The event (or event ID) to check.
    :param name: The name of the feature.
    """
    from MaKaC.conference import ConferenceHolder
    feature = get_feature_definition(name)
    enabled_features = features_event_settings.get(event, 'enabled')
    if enabled_features is not None:
        return feature.name in enabled_features
    else:
        with DBMgr.getInstance().global_connection():
            if isinstance(event, (basestring, int, long)):
                event = ConferenceHolder().getById(event, True)
            return event and feature.is_default_for_event(event)


def require_feature(event, name):
    """Raises a NotFound error if a feature is not enabled

    :param event: The event (or event ID) to check.
    :param name: The name of the feature.
    """
    if not is_feature_enabled(event, name):
        feature = get_feature_definition(name)
        raise NotFound("The '{}' feature is not enabled for this event.".format(feature.friendly_name))

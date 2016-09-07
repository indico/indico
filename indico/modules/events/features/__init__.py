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

from flask import session

from indico.core import signals
from indico.core.logger import Logger
from indico.modules.events.settings import EventSettingsProxy
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem

logger = Logger.get('events.features')
event_settings = EventSettingsProxy('features', {
    'enabled': None
})


@signals.menu.items.connect_via('event-management-sidemenu')
def _extend_event_management_menu(sender, event, **kwargs):
    if not event.can_manage(session.user):
        return
    return SideMenuItem('features', 'Features', url_for('event_features.index', event), section='advanced')


@signals.app_created.connect
def _check_feature_definitions(app, **kwargs):
    # This will raise RuntimeError if the feature names are not unique
    from indico.modules.events.features.util import get_feature_definitions
    get_feature_definitions()


@signals.event.type_changed.connect
def _event_type_changed(event, **kwargs):
    from indico.modules.events.features.util import (get_enabled_features, get_disallowed_features, set_feature_enabled,
                                                     format_feature_names)
    for feature in get_enabled_features(event, only_explicit=True) & get_disallowed_features(event):
        set_feature_enabled(event, feature, False)

# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

import warnings

from flask import session
from pytz import utc

from indico.core import signals
from indico.core.config import Config
from indico.modules.events.cloning import EventCloner
from indico.modules.events.features import features_event_settings
from indico.modules.events.operations import create_event
from indico.util.string import return_ascii


def warn_on_access(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if Config.getInstance().getDebug():
            warnings.warn('Called {}'.format(fn.__name__), stacklevel=2)
        return fn(*args, **kwargs)

    return wrapper


class LegacyConference(object):
    def __init__(self, event):
        self.event = event

    @return_ascii
    def __repr__(self):
        return '<Conference: {}>'.format(self.event)

    @property
    def id(self):
        return self.event.id

    @property
    def as_event(self):
        return self.event

    @warn_on_access
    def getId(self):
        return self.id

    @property
    @warn_on_access
    def locator(self):
        warnings.warn('Accessed Conference.locator', stacklevel=4)
        return self.event.locator

    def clone(self, startDate):
        # startDate is in the timezone of the event
        old_event = self.as_event
        start_dt = old_event.tzinfo.localize(startDate).astimezone(utc)
        end_dt = start_dt + old_event.duration
        data = {
            'start_dt': start_dt,
            'end_dt': end_dt,
            'timezone': old_event.timezone,
            'title': old_event.title,
            'description': old_event.description,
            'visibility': old_event.visibility
        }
        event = create_event(old_event.category, old_event.type_, data,
                             features=features_event_settings.get(self, 'enabled'),
                             add_creator_as_manager=False)

        # Run the new modular cloning system
        EventCloner.run_cloners(old_event, event)
        signals.event.cloned.send(old_event, new_event=event)

        # Grant access to the event creator -- must be done after modular cloners
        # since cloning the event ACL would result in a duplicate entry
        with event.logging_disabled:
            event.update_principal(session.user, full_access=True)

        return event.as_legacy

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

from __future__ import unicode_literals

from indico.core import signals
from indico.util.signals import named_objects_from_signal


def get_request_definitions():
    """Returns a dict of request definitions"""
    return named_objects_from_signal(signals.plugin.get_event_request_definitions.send(), plugin_attr='plugin')


def is_request_manager(user):
    """Checks if the user manages any request types"""
    if not user:
        return False
    return any(def_.can_be_managed(user) for def_ in get_request_definitions().itervalues())

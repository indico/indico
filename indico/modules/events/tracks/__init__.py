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
from indico.core.roles import ManagementRole
from indico.modules.events import Event
from indico.modules.events.models.events import EventType
from indico.modules.events.tracks.clone import TrackCloner
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('tracks')


@signals.menu.items.connect_via('event-management-sidemenu')
def _sidemenu_items(sender, event, **kwargs):
    if event.type_ == EventType.conference and event.can_manage(session.user):
        return SideMenuItem('program', _('Programme'), url_for('tracks.manage', event), section='organization')


@signals.acl.can_access.connect_via(Event)
def _can_access_event(cls, obj, user, authorized, **kwargs):
    """Give track reviewers access to the event"""
    if not user or authorized is None or authorized:
        return
    avatar = user.as_avatar
    if any(track.isCoordinator(avatar) for track in obj.as_legacy.getTrackList()):
        return True


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    target.abstract_reviewer_for_tracks |= source.abstract_reviewer_for_tracks
    source.abstract_reviewer_for_tracks.clear()
    target.convener_for_tracks |= source.convener_for_tracks
    source.convener_for_tracks.clear()


@signals.event_management.get_cloners.connect
def _get_cloners(sender, **kwargs):
    yield TrackCloner


@signals.acl.get_management_roles.connect_via(Event)
def _get_management_roles(sender, **kwargs):
    return TrackConvenerRole


class TrackConvenerRole(ManagementRole):
    name = 'track_convener'
    friendly_name = _('Track convener')
    description = _('Grants track convener rights in an event')

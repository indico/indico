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

from flask import session

from indico.core import signals
from indico.core.config import config
from indico.core.permissions import ManagementPermission
from indico.modules.rb import Room, rb_settings
from indico.modules.rb.models.blocking_principals import BlockingPrincipal
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.models.principals import RoomPrincipal
from indico.modules.rb.models.reservations import Reservation, ReservationLink
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem, TopMenuItem


@signals.menu.items.connect_via('top-menu')
def _topmenu_items(sender, **kwargs):
    if config.ENABLE_ROOMBOOKING:
        yield TopMenuItem('rb_new', _('Room booking'), url_for('rooms_new.roombooking'), 80)


@signals.menu.items.connect_via('event-management-sidemenu')
def _sidemenu_items(sender, event, **kwargs):
    if config.ENABLE_ROOMBOOKING and event.can_manage(session.user):
        yield SideMenuItem('room_booking', _('Room Booking'), url_for('rooms_new.event_booking_list', event), 50,
                           icon='location')


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    Blocking.query.filter_by(created_by_id=source.id).update({Blocking.created_by_id: target.id})
    BlockingPrincipal.merge_users(target, source, 'blocking')
    Reservation.query.filter_by(created_by_id=source.id).update({Reservation.created_by_id: target.id})
    Reservation.query.filter_by(booked_for_id=source.id).update({Reservation.booked_for_id: target.id})
    Room.query.filter_by(owner_id=source.id).update({Room.owner_id: target.id})
    RoomPrincipal.merge_users(target, source, 'room')
    rb_settings.acls.merge_users(target, source)


@signals.event.deleted.connect
def _event_deleted(event, user, **kwargs):
    reservation_links = (event.all_room_reservation_links
                         .join(Reservation)
                         .filter(~ReservationLink.is_rejected, ~ReservationLink.is_cancelled)
                         .all())
    for link in reservation_links:
        link.reservation.cancel(user or session.user, 'Associated event was deleted')


class BookPermission(ManagementPermission):
    name = 'book'
    friendly_name = _('Book')
    description = _('Allows booking the room')
    user_selectable = True


class PrebookPermission(ManagementPermission):
    name = 'prebook'
    friendly_name = _('Prebook')
    description = _('Allows prebooking the room')
    user_selectable = True


class OverridePermission(ManagementPermission):
    name = 'override'
    friendly_name = _('Override')
    description = _('Allows overriding restrictions when booking the room')
    user_selectable = True


class ModeratePermission(ManagementPermission):
    name = 'moderate'
    friendly_name = _('Moderate')
    description = _('Allows moderating bookings (approving/rejecting/editing)')
    user_selectable = True


@signals.acl.get_management_permissions.connect_via(Room)
def _get_management_permissions(sender, **kwargs):
    yield BookPermission
    yield PrebookPermission
    yield OverridePermission
    yield ModeratePermission

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
from indico.core.logger import Logger
from indico.core.settings import SettingsProxy
from indico.modules.rb.models.blocking_principals import BlockingPrincipal
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.util import rb_is_admin
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem, SideMenuSection, TopMenuItem


logger = Logger.get('rb')


rb_settings = SettingsProxy('roombooking', {
    'google_maps_api_key': '',
    'assistance_emails': [],
    'vc_support_emails': [],
    'notification_before_days': 2,
    'notification_before_days_weekly': 5,
    'notification_before_days_monthly': 7,
    'notifications_enabled': True,
    'booking_limit': 365
}, acls={'admin_principals', 'authorized_principals'})


@signals.import_tasks.connect
def _import_tasks(sender, **kwargs):
    import indico.modules.rb.tasks


@signals.menu.items.connect_via('admin-sidemenu')
def _extend_admin_menu(sender, **kwargs):
    if not config.ENABLE_ROOMBOOKING:
        return
    if session.user.is_admin:
        yield SideMenuItem('rb-settings', _("Settings"), url_for('rooms_admin.settings'),
                           section='roombooking', icon='location')
        yield SideMenuItem('rb-rooms', _("Rooms"), url_for('rooms_admin.roomBooking-admin'),
                           section='roombooking', icon='location')
    else:
        yield SideMenuItem('rb-rooms', _("Rooms"), url_for('rooms_admin.roomBooking-admin'), 70, icon='location')


@signals.menu.items.connect_via('top-menu')
def _topmenu_items(sender, **kwargs):
    if config.ENABLE_ROOMBOOKING:
        yield TopMenuItem('rb', _('Room booking'), url_for('rooms.roomBooking'), 80)


@signals.menu.sections.connect_via('admin-sidemenu')
def _sidemenu_sections(sender, **kwargs):
    yield SideMenuSection('roombooking', _("Room Booking"), 70, icon='location')


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    BlockingPrincipal.merge_users(target, source, 'blocking')
    Blocking.find(created_by_id=source.id).update({Blocking.created_by_id: target.id})
    Reservation.find(created_by_id=source.id).update({Reservation.created_by_id: target.id})
    Reservation.find(booked_for_id=source.id).update({Reservation.booked_for_id: target.id})
    Room.find(owner_id=source.id).update({Room.owner_id: target.id})
    rb_settings.acls.merge_users(target, source)


@signals.event.deleted.connect
def _event_deleted(event, user, **kwargs):
    reservations = (Reservation.query.with_parent(event)
                    .filter(~Reservation.is_cancelled,
                            ~Reservation.is_rejected)
                    .all())
    for resv in reservations:
        resv.cancel(user or session.user, 'Associated event was deleted')


@signals.menu.sections.connect_via('rb-sidemenu')
def _sidemenu_sections(sender, **kwargs):
    user_has_rooms = session.user is not None and Room.user_owns_rooms(session.user)

    yield SideMenuSection('search', _("Search"), 40, icon='search', active=True)
    if user_has_rooms:
        yield SideMenuSection('my_rooms', _("My Rooms"), 30, icon='user')
    yield SideMenuSection('blocking', _("Room Blocking"), 20, icon='lock')


@signals.menu.items.connect_via('rb-sidemenu')
def _sidemenu_items(sender, **kwargs):
    user_is_admin = session.user is not None and rb_is_admin(session.user)
    user_has_rooms = session.user is not None and Room.user_owns_rooms(session.user)
    map_available = Location.default_location is not None and Location.default_location.is_map_available

    yield SideMenuItem('book_room', _('Book a Room'), url_for('rooms.book'), 80, icon='checkmark')
    if map_available:
        yield SideMenuItem('map', _('Map of Rooms'), url_for('rooms.roomBooking-mapOfRooms'), 70, icon='location')
    yield SideMenuItem('calendar', _('Calendar'), url_for('rooms.calendar'), 60, icon='calendar')
    yield SideMenuItem('my_bookings', _('My Bookings'), url_for('rooms.my_bookings'), 50, icon='time')
    yield SideMenuItem('search_bookings', _('Search bookings'), url_for('rooms.roomBooking-search4Bookings'),
                       section='search')
    yield SideMenuItem('search_rooms', _('Search rooms'), url_for('rooms.search_rooms'),
                       section='search')
    if user_has_rooms:
        yield SideMenuItem('bookings_in_my_rooms', _('Bookings in my rooms'), url_for('rooms.bookings_my_rooms'),
                           section='my_rooms')
        yield SideMenuItem('prebookings_in_my_rooms', _('Pre-bookings in my rooms'),
                           url_for('rooms.pending_bookings_my_rooms'),
                           section='my_rooms')
        yield SideMenuItem('room_list', _('Room list'), url_for('rooms.search_my_rooms'),
                           section='my_rooms')
    yield SideMenuItem('my_blockings', _('My Blockings'),
                       url_for('rooms.blocking_list', only_mine=True, timeframe='recent'),
                       section='blocking')
    if user_has_rooms:
        yield SideMenuItem('blockings_my_rooms', _('Blockings for my rooms'), url_for('rooms.blocking_my_rooms'),
                           section='blocking')
    yield SideMenuItem('blocking_create', _('Block rooms'), url_for('rooms.create_blocking'), section='blocking')
    if user_is_admin:
        yield SideMenuItem('admin', _('Administration'), url_for('rooms_admin.roomBooking-admin'), 10,
                           icon='user-chairperson')

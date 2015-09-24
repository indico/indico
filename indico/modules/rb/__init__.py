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

from flask import session

from indico.core import signals
from indico.core.logger import Logger
from indico.core.settings import SettingsProxy
from indico.modules.rb.models.blocking_principals import BlockingPrincipal
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.util import rb_is_admin
from indico.web.flask.util import url_for
from indico.util.i18n import _
from indico.web.menu import SideMenuSection, SideMenuItem


logger = Logger.get('rb')


settings = SettingsProxy('roombooking', {
    'assistance_emails': [],
    'vc_support_emails': [],
    'notification_hour': 6,
    'notification_before_days': 1,
    'notifications_enabled': True
}, acls={'admin_principals', 'authorized_principals'})


@signals.import_tasks.connect
def _import_tasks(sender, **kwargs):
    import indico.modules.rb.tasks


@signals.menu.items.connect_via('admin-sidemenu')
def _extend_admin_menu(sender, **kwargs):
    return 'rb', SideMenuItem(_("Rooms"), url_for('rooms_admin.settings'), 70, icon='location')


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    BlockingPrincipal.merge_users(target, source, 'blocking')
    Blocking.find(created_by_id=source.id).update({Blocking.created_by_id: target.id})
    Reservation.find(created_by_id=source.id).update({Reservation.created_by_id: target.id})
    Reservation.find(booked_for_id=source.id).update({Reservation.booked_for_id: target.id})
    Room.find(owner_id=source.id).update({Room.owner_id: target.id})
    settings.acls.merge_users(target, source)


@signals.event.deleted.connect
def _event_deleted(event, user, **kwargs):
    reservations = Reservation.find(Reservation.event_id == int(event.id),
                                    ~Reservation.is_cancelled,
                                    ~Reservation.is_rejected)
    for resv in reservations:
        resv.cancel(user or session.user, 'Associated event was deleted')


@signals.menu.sections.connect_via('rb-sidemenu')
def _sidemenu_sections(sender, **kwargs):
    user_has_rooms = session.user is not None and Room.user_owns_rooms(session.user)

    yield 'search', SideMenuSection(_("Search"), 40, icon='search', active=True)
    yield 'my_rooms', SideMenuSection(_("My Rooms"), 30, icon='user', visible=user_has_rooms)
    yield 'blocking', SideMenuSection(_("Room Blocking"), 20, icon='lock')


@signals.menu.items.connect_via('rb-sidemenu')
def _sidemenu_items(sender, **kwargs):
    user_is_admin = session.user is not None and rb_is_admin(session.user)
    map_available = Location.default_location is not None and Location.default_location.is_map_available

    yield 'book_room', SideMenuItem(_('Book a Room'), url_for('rooms.book'), 80, icon='checkmark')
    yield 'map', SideMenuItem(_('Map of Rooms'), url_for('rooms.roomBooking-mapOfRooms'),
                              70, icon='location', visible=map_available)
    yield 'calendar', SideMenuItem(_('Calendar'), url_for('rooms.calendar'), 60, icon='calendar')
    yield 'my_bookings', SideMenuItem(_('My Bookings'), url_for('rooms.my_bookings'), 50, icon='time')
    yield 'search_bookings', SideMenuItem(_('Search bookings'), url_for('rooms.roomBooking-search4Bookings'),
                                          section='search')
    yield 'search_rooms', SideMenuItem(_('Search rooms'), url_for('rooms.search_rooms'),
                                       section='search')
    yield 'bookings_in_my_rooms', SideMenuItem(_('Bookings in my rooms'), url_for('rooms.bookings_my_rooms'),
                                               section='my_rooms')
    yield 'prebookings_in_my_rooms', SideMenuItem(_('Pre-bookings in my rooms'),
                                                  url_for('rooms.pending_bookings_my_rooms'),
                                                  section='my_rooms')
    yield 'room_list', SideMenuItem(_('Room list'), url_for('rooms.search_my_rooms'),
                                    section='my_rooms')
    yield 'my_blockings', SideMenuItem(_('My Blockings'),
                                       url_for('rooms.blocking_list', only_mine=True, timeframe='recent'),
                                       section='blocking')
    yield 'blockings_my_rooms', SideMenuItem(_('Blockings for my rooms'),
                                             url_for('rooms.blocking_my_rooms'),
                                             section='blocking')
    yield 'blocking_create', SideMenuItem(_('Block rooms'), url_for('rooms.create_blocking'),
                                          section='blocking')
    yield 'admin', SideMenuItem(_('Administration'), url_for('rooms_admin.roomBooking-admin'),
                                10, icon='user-chairperson', visible=user_is_admin)

# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import session

from indico.core import signals
from indico.core.config import config
from indico.core.logger import Logger
from indico.core.permissions import ManagementPermission, check_permissions
from indico.core.settings import SettingsProxy
from indico.core.settings.converters import ModelListConverter
from indico.modules.categories.models.categories import Category
from indico.modules.rb.models.rooms import Room
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem, TopMenuItem


logger = Logger.get('rb')


rb_settings = SettingsProxy('roombooking', {
    'managers_edit_rooms': False,
    'excluded_categories': [],
    'notification_before_days': 2,
    'notification_before_days_weekly': 5,
    'notification_before_days_monthly': 7,
    'notifications_enabled': True,
    'end_notification_daily': 1,
    'end_notification_weekly': 3,
    'end_notification_monthly': 7,
    'end_notifications_enabled': True,
    'booking_limit': 365,
    'tileserver_url': None,
    'grace_period': None,
}, acls={
    'admin_principals',
    'authorized_principals'
}, converters={
    'excluded_categories': ModelListConverter(Category)
})


@signals.import_tasks.connect
def _import_tasks(sender, **kwargs):
    import indico.modules.rb.tasks  # noqa: F401


@signals.users.preferences.connect
def _get_extra_user_prefs(sender, **kwargs):
    from indico.modules.rb.user_prefs import RBUserPreferences
    if config.ENABLE_ROOMBOOKING:
        return RBUserPreferences


@signals.menu.items.connect_via('admin-sidemenu')
def _extend_admin_menu(sender, **kwargs):
    if config.ENABLE_ROOMBOOKING and session.user.is_admin:
        url = url_for('rb.roombooking', path='admin')
        return SideMenuItem('rb', _('Room Booking'), url, 70, icon='location')


@signals.menu.items.connect_via('top-menu')
def _topmenu_items(sender, **kwargs):
    if config.ENABLE_ROOMBOOKING:
        yield TopMenuItem('room_booking', _('Room booking'), url_for('rb.roombooking'), 80)


@signals.menu.items.connect_via('event-management-sidemenu')
def _sidemenu_items(sender, event, **kwargs):
    if config.ENABLE_ROOMBOOKING and event.can_manage(session.user):
        yield SideMenuItem('room_booking', _('Room Booking'), url_for('rb.event_booking_list', event), 50,
                           icon='location')


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    from indico.modules.rb.models.blocking_principals import BlockingPrincipal
    from indico.modules.rb.models.blockings import Blocking
    from indico.modules.rb.models.principals import RoomPrincipal
    from indico.modules.rb.models.reservations import Reservation
    Blocking.query.filter_by(created_by_id=source.id).update({Blocking.created_by_id: target.id})
    BlockingPrincipal.merge_users(target, source, 'blocking')
    Reservation.query.filter_by(created_by_id=source.id).update({Reservation.created_by_id: target.id})
    Reservation.query.filter_by(booked_for_id=source.id).update({Reservation.booked_for_id: target.id})
    Room.query.filter_by(owner_id=source.id).update({Room.owner_id: target.id})
    RoomPrincipal.merge_users(target, source, 'room')
    rb_settings.acls.merge_users(target, source)


@signals.event.deleted.connect
def _event_deleted(event, user, **kwargs):
    from indico.modules.rb.models.reservations import Reservation
    reservation_links = (event.all_room_reservation_links
                         .join(Reservation)
                         .filter(~Reservation.is_rejected, ~Reservation.is_cancelled)
                         .all())
    for link in reservation_links:
        link.reservation.cancel(user or session.user, 'Associated event was deleted')


class BookPermission(ManagementPermission):
    name = 'book'
    friendly_name = _('Book')
    description = _('Allows booking the room')
    user_selectable = True
    color = 'green'


class PrebookPermission(ManagementPermission):
    name = 'prebook'
    friendly_name = _('Prebook')
    description = _('Allows prebooking the room')
    user_selectable = True
    default = True
    color = 'orange'


class OverridePermission(ManagementPermission):
    name = 'override'
    friendly_name = _('Override')
    description = _('Allows overriding restrictions when booking the room')
    user_selectable = True
    color = 'pink'


class ModeratePermission(ManagementPermission):
    name = 'moderate'
    friendly_name = _('Moderate')
    description = _('Allows moderating bookings (approving/rejecting/editing)')
    user_selectable = True
    color = 'purple'


@signals.acl.get_management_permissions.connect_via(Room)
def _get_management_permissions(sender, **kwargs):
    yield BookPermission
    yield PrebookPermission
    yield OverridePermission
    yield ModeratePermission


@signals.app_created.connect
def _check_permissions(app, **kwargs):
    check_permissions(Room)

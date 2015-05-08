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
from indico.core.models.settings import SettingsProxy
from indico.modules.rb.models.blocking_principals import BlockingPrincipal
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.rooms import Room
from indico.util.user import principals_merge_users


settings = SettingsProxy('roombooking', {
    'admin_principals': [],
    'authorized_principals': [],
    'assistance_emails': [],
    'vc_support_emails': [],
    'notification_hour': 6,
    'notification_before_days': 1,
    'notifications_enabled': True
})


@signals.merge_users.connect
def _merge_users(user, merged, **kwargs):
    target = user.user
    source = merged.user
    for bp in BlockingPrincipal.find():
        if bp.principal == source:
            bp.principal = target
    Blocking.find(created_by_id=source.id).update({Blocking.created_by_id: target.id})
    Reservation.find(created_by_id=source.id).update({Reservation.created_by_id: target.id})
    Reservation.find(booked_for_id=source.id).update({Reservation.booked_for_id: target.id})
    Room.find(owner_id=source.id).update({Room.owner_id: target.id})
    for key in ('authorized_principals', 'admin_principals'):
        principals = settings.get(key)
        principals = principals_merge_users(principals, target.id, source.id)
        settings.set(key, principals)


@signals.event.deleted.connect
def _event_deleted(event, user, **kwargs):
    if not event.id.isdigit():
        return
    reservations = Reservation.find(Reservation.event_id == int(event.id),
                                    ~Reservation.is_cancelled,
                                    ~Reservation.is_rejected)
    for resv in reservations:
        resv.event_id = None
        resv.cancel(user or session.user, 'Associated event was deleted')

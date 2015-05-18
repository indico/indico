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
from sqlalchemy.orm import joinedload

from indico.core import signals
from indico.core.db import db
from indico.core.settings import SettingsProxy
from indico.modules.rb.models.blocking_principals import BlockingPrincipal
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.rooms import Room


settings = SettingsProxy('roombooking', {
    'assistance_emails': [],
    'vc_support_emails': [],
    'notification_hour': 6,
    'notification_before_days': 1,
    'notifications_enabled': True
}, acls={'admin_principals', 'authorized_principals'})


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    source_principals = set(source.in_blocking_acls.options(joinedload(BlockingPrincipal.blocking)))
    target_blockings = {x.blocking for x in target.in_blocking_acls.options(joinedload(BlockingPrincipal.blocking))}
    for principal in source_principals:
        if principal.blocking not in target_blockings:
            principal.user_id = target.id
        else:
            db.session.delete(principal)
    Blocking.find(created_by_id=source.id).update({Blocking.created_by_id: target.id})
    Reservation.find(created_by_id=source.id).update({Reservation.created_by_id: target.id})
    Reservation.find(booked_for_id=source.id).update({Reservation.booked_for_id: target.id})
    Room.find(owner_id=source.id).update({Room.owner_id: target.id})
    settings.acls.merge_users(target, source)


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

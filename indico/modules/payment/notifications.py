# This file is part of Indico.
# Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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

from flask import render_template

from indico.core.notifications import email_sender, make_email
from MaKaC.conference import ConferenceHolder


@email_sender
def notify_double_payment(event_id, registrant_id):
    event = ConferenceHolder().getById(event_id)
    registrant = event.getRegistrantById(registrant_id)
    if not registrant:
        return
    to = event.getCreator().getEmail()
    body = render_template('payment/emails/double_payment_email_to_manager.txt', event=event, registrant=registrant)
    return make_email(to, subject="Double payment detected", body=body)

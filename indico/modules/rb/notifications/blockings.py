# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import render_template

from indico.core.notifications import email_sender, make_email


@email_sender
def notify_request(owner, blocking, blocked_rooms):
    """Notify room owner about blockings he has to approve.

    Expect only blockings for rooms owned by the specified owner.
    """
    subject = 'Confirm room blockings'
    body = render_template('rb/emails/blockings/awaiting_confirmation_email_to_manager.txt',
                           owner=owner, blocking=blocking, blocked_rooms=blocked_rooms)
    return make_email(owner.email, subject=subject, body=body)


@email_sender
def notify_request_response(blocked_room):
    """
    Notify blocking creator about approval/rejection of his
    blocking request for a room.
    """
    to = blocked_room.blocking.created_by_user.email
    verb = blocked_room.State(blocked_room.state).title.upper()
    subject = 'Room blocking {}'.format(verb)
    body = render_template('rb/emails/blockings/state_email_to_user.txt',
                           blocking=blocked_room.blocking, blocked_room=blocked_room, verb=verb)
    return make_email(to, subject=subject, body=body)

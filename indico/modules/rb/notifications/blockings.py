from flask import render_template

from indico.core.config import Config
from indico.modules.rb.notifications.util import email_sender


@email_sender
def notify_request(owner, blocking, blocked_rooms):
    """
    Notifies (e-mails) room owner about blockings he has to approve.
    Expects only blockings for rooms owned by the specified owner
    """
    from_addr = Config.getInstance().getNoReplyEmail()
    to = owner.getEmail()
    subject = 'Confirm room blockings'
    body = render_template('rb/emails/blockings/awaiting_confirmation_email_to_manager.txt',
                           owner=owner, blocking=blocking, blocked_rooms=blocked_rooms)
    return {
        'fromAddr': from_addr,
        'toList': [to],
        'subject': subject,
        'body': body
    }


@email_sender
def notify_request_response(blocked_room):
    """
    Notifies (e-mails) blocking creator about approval/rejection of his
    blocking request for a room
    """
    from_addr = Config.getInstance().getSupportEmail()
    to = blocked_room.blocking.created_by_user.getEmail()
    verb = blocked_room.State(blocked_room.state).title.upper()
    subject = 'Room blocking {}'.format(verb)
    body = render_template('rb/emails/blockings/state_email_to_user.txt',
                           blocking=blocked_room.blocking, blocked_room=blocked_room, verb=verb)
    return {
        'fromAddr': from_addr,
        'toList': [to],
        'subject': subject,
        'body': body
    }

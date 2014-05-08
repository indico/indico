from indico.core.config import Config
from MaKaC.webinterface.wcomponents import WTemplated


def request_confirmation(owner, blocking, blocked_rooms):
    """
    Notifies (e-mails) room owner about blockings he has to approve.
    Expects only blockings for rooms owned by the specified owner
    """
    to = owner.getEmail()
    subject = 'Confirm room blockings'
    wc = WTemplated('RoomBookingEmail_2ResponsibleConfirmBlocking')
    text = wc.getHTML({
        'owner': owner,
        'blocking': blocking,
        'blocked_rooms': blocked_rooms
    })
    from_addr = Config.getInstance().getNoReplyEmail()
    return {
        'fromAddr': from_addr,
        'toList': [to],
        'subject': subject,
        'body': text
    }


def blocking_processed(blocked_room):
    """
    Notifies (e-mails) blocking creator about approval/rejection of his
    blocking request for a room
    """
    to = blocked_room.blocking.created_by_user.getEmail()
    verb = blocked_room.State(blocked_room.state).title.upper()
    subject = 'Room blocking {}'.format(verb)
    wc = WTemplated('RoomBookingEmail_2BlockingCreatorRequestProcessed')
    text = wc.getHTML({
        'blocking': blocked_room.blocking,
        'blocked_room': blocked_room,
        'verb': verb
    })
    from_addr = Config.getInstance().getSupportEmail()
    return {
        'fromAddr': from_addr,
        'toList': [to],
        'subject': subject,
        'body': text
    }

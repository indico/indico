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

from indico.core.config import Config
from indico.web.flask.templating import get_template_module, get_overridable_template_name
from indico.modules.vc.util import get_linked_to_description

from MaKaC.common.mail import GenericMailer
from MaKaC.webinterface.mail import GenericNotification


def notify_created(plugin, room, room_assoc, event, user):
    """Notifies about the creation of a vc_room.

    :param room: the vc_room
    :param event: the event
    :param user: the user performing the action
    """

    name = get_overridable_template_name('emails/created.html', plugin, core_prefix='vc/')
    tpl = get_template_module(name, plugin=plugin, vc_room=room, event=event, vc_room_event=room_assoc, user=user,
                              linked_to_title=get_linked_to_description(room_assoc))
    _send('create', user, plugin, event, room, tpl.get_subject(), tpl.get_body())


def notify_deleted(plugin, room, room_assoc, event, user):
    """Notifies about the deletion of a vc_room from the system.

    :param room: the vc_room
    :param event: the event
    :param user: the user performing the action
    """
    name = get_overridable_template_name('emails/deleted.html', plugin, core_prefix='vc/')
    tpl = get_template_module(name, plugin=plugin, vc_room=room, event=event, vc_room_event=room_assoc, user=user)
    _send('create', user, plugin, event, room, tpl.get_subject(), tpl.get_body())


def _send(action, user, plugin, event, room, subject, body):
    to_list = {user.getEmail()}
    cc_list = plugin.get_notification_cc_list(action, room, event) - to_list
    bcc_list = plugin.get_notification_bcc_list(action, room, event) - cc_list - to_list

    notification = {
        'content-type': 'text/html',
        'fromAddr': Config.getInstance().getNoReplyEmail(),
        'toList': to_list,
        'ccList': cc_list,
        'bccList': bcc_list,
        'subject': subject,
        'body': body
    }
    if event is None:
        GenericMailer.send(GenericNotification(notification))
    else:
        GenericMailer.sendAndLog(GenericNotification(notification),
                                 event, plugin.name)

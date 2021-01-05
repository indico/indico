# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.notifications import make_email, send_email
from indico.modules.vc.util import get_linked_to_description
from indico.web.flask.templating import get_overridable_template_name, get_template_module


def notify_created(plugin, room, room_assoc, event, user):
    """Notify about the creation of a vc_room.

    :param room: the vc_room
    :param event: the event
    :param user: the user performing the action
    """

    name = get_overridable_template_name('emails/created.html', plugin, core_prefix='vc/')
    tpl = get_template_module(name, plugin=plugin, vc_room=room, event=event, vc_room_event=room_assoc, user=user,
                              linked_to_title=get_linked_to_description(room_assoc))
    _send('create', user, plugin, event, room, tpl)


def notify_deleted(plugin, room, room_assoc, event, user):
    """Notify about the deletion of a vc_room from the system.

    :param room: the vc_room
    :param event: the event
    :param user: the user performing the action
    """
    name = get_overridable_template_name('emails/deleted.html', plugin, core_prefix='vc/')
    tpl = get_template_module(name, plugin=plugin, vc_room=room, event=event, vc_room_event=room_assoc, user=user)
    _send('delete', user, plugin, event, room, tpl)


def _send(action, user, plugin, event, room, template_module):
    to_list = {user.email}
    cc_list = plugin.get_notification_cc_list(action, room, event) - to_list
    bcc_list = plugin.get_notification_bcc_list(action, room, event) - cc_list - to_list

    email = make_email(to_list, cc_list, bcc_list, template=template_module, html=True)
    send_email(email, event, plugin.friendly_name)

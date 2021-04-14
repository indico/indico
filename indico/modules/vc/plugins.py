# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re

from flask import render_template
from flask_pluginengine import render_plugin_template

from indico.core import signals
from indico.modules.events.contributions import Contribution
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.vc.forms import VCPluginSettingsFormBase
from indico.modules.vc.models.vc_rooms import VCRoomEventAssociation, VCRoomLinkType
from indico.util.decorators import classproperty
from indico.web.flask.templating import get_overridable_template_name
from indico.web.forms.base import FormDefaults


PREFIX_RE = re.compile('^vc_')


class VCPluginMixin:
    settings_form = VCPluginSettingsFormBase
    default_settings = {'notification_emails': []}
    acl_settings = {'acl', 'managers'}
    #: the :class:`IndicoForm` to use for the videoconference room form
    vc_room_form = None
    #: the :class:`IndicoForm` to use for the videoconference room attach form
    vc_room_attach_form = None
    #: the readable name of the VC plugin
    friendly_name = None

    def init(self):
        super().init()
        if not self.name.startswith('vc_'):
            raise Exception('Videoconference plugins must be named vc_*')
        self.connect(signals.users.merged, self._merge_users)

    @property
    def service_name(self):
        return PREFIX_RE.sub('', self.name)

    @property
    def logo_url(self):
        raise NotImplementedError('VC plugin must have a logo URL')

    @property
    def icon_url(self):
        raise NotImplementedError('VC plugin must have an icon URL')

    @classproperty
    @staticmethod
    def category():
        from indico.core.plugins import PluginCategory
        return PluginCategory.videoconference

    def get_vc_room_form_defaults(self, event):
        return {
            'name': event.title,
            'show': True,
            'linking': 'event',
            'contribution': '',
            'block': ''
        }

    def get_vc_room_attach_form_defaults(self, event):
        return {
            'room': None,
            'contribution': None,
            'block': None,
            'linking': 'event',
            'show': True
        }

    def get_notification_cc_list(self, action, vc_room, event):
        return set()

    def get_notification_bcc_list(self, action, vc_room, event):
        return set(self.settings.get('notification_emails', set()))

    def render_form(self, **kwargs):
        """Render the videoconference room form.

        :param kwargs: arguments passed to the template
        """
        return render_template('vc/manage_event_create_room.html', **kwargs)

    def render_info_box(self, vc_room, event_vc_room, event, **kwargs):
        """Render the information shown in the expandable box of a VC room row.

        :param vc_room: the VC room object
        :param event_vc_room: the association of an event and a VC room
        :param event: the event with the current VC room attached to it
        :param kwargs: arguments passed to the template
        """
        return render_plugin_template(f'{self.name}:info_box.html', plugin=self, event_vc_room=event_vc_room,
                                      event=event, vc_room=vc_room, settings=self.settings, **kwargs)

    def render_manage_event_info_box(self, vc_room, event_vc_room, event, **kwargs):
        """
        Render the information shown in the expandable box on a
        VC room in the management area.

        :param vc_room: the VC room object
        :param event_vc_room: the association of an event and a VC room
        :param event: the event with the current VC room attached to it
        :param kwargs: arguments passed to the template
        """
        return render_plugin_template(f'{self.name}:manage_event_info_box.html', plugin=self,
                                      event_vc_room=event_vc_room, event=event, vc_room=vc_room,
                                      settings=self.settings, **kwargs)

    def render_buttons(self, vc_room, event_vc_room, **kwargs):
        """
        Render a list of plugin specific buttons (eg: Join URL, etc)
        in the management area.

        :param vc_room: the VC room object
        :param event_vc_room: the association of an event and a VC room
        :param kwargs: arguments passed to the template
        """
        name = get_overridable_template_name('management_buttons.html', self, core_prefix='vc/')
        return render_template(name, plugin=self, vc_room=vc_room, event_vc_room=event_vc_room, **kwargs)

    def get_extra_delete_msg(self, vc_room, event_vc_room):
        """
        Return a custom message to show in the confirmation dialog
        when deleting a VC room.

        :param vc_room: the VC room object
        :param event_vc_room: the association of an event and a VC room
        :return: a string (may contain HTML) with the message to display
        """
        return ''

    def render_event_buttons(self, vc_room, event_vc_room, **kwargs):
        """
        Render a list of plugin specific buttons (eg: Join URL, etc)
        in the event page.

        :param vc_room: the VC room object
        :param event_vc_room: the association of an event and a VC room
        :param kwargs: arguments passed to the template
        """
        name = get_overridable_template_name('event_buttons.html', self, core_prefix='vc/')
        return render_template(name, plugin=self, vc_room=vc_room, event_vc_room=event_vc_room,
                               event=event_vc_room.event, **kwargs)

    def create_form(self, event, existing_vc_room=None, existing_event_vc_room=None):
        """Create the videoconference room form.

        :param event: the event the videoconference room is for
        :param existing_vc_room: a vc_room from which to retrieve data for the form
        :return: an instance of an :class:`IndicoForm` subclass
        """
        if existing_vc_room and existing_event_vc_room:
            kwargs = {
                'name': existing_vc_room.name,
                'linking': existing_event_vc_room.link_type.name,
                'show': existing_event_vc_room.show
            }

            if existing_event_vc_room.link_type == VCRoomLinkType.contribution:
                kwargs['contribution'] = existing_event_vc_room.contribution_id
            elif existing_event_vc_room.link_type == VCRoomLinkType.block:
                kwargs['block'] = existing_event_vc_room.session_block_id

            data = existing_vc_room.data
            data.update(existing_event_vc_room.data)

            defaults = FormDefaults(data, **kwargs)
        else:
            defaults = FormDefaults(self.get_vc_room_form_defaults(event))
        with self.plugin_context():
            return self.vc_room_form(prefix='vc-', obj=defaults, event=event, vc_room=existing_vc_room)

    def update_data_association(self, event, vc_room, event_vc_room, data):
        contribution_id = data.pop('contribution')
        block_id = data.pop('block')
        link_type = VCRoomLinkType[data.pop('linking')]

        if link_type == VCRoomLinkType.event:
            event_vc_room.link_object = event
        elif link_type == VCRoomLinkType.contribution:
            event_vc_room.link_object = Contribution.get_or_404(contribution_id)
        elif link_type == VCRoomLinkType.block:
            event_vc_room.link_object = SessionBlock.get_or_404(block_id)
        event_vc_room.vc_room = vc_room
        event_vc_room.show = data.pop('show')
        if event_vc_room.data is None:
            event_vc_room.data = {}

    def update_data_vc_room(self, vc_room, data, is_new=False):
        if 'name' in data:
            vc_room.name = data.pop('name')

        if vc_room.data is None:
            vc_room.data = {}

    def create_room(self, vc_room, event):
        raise NotImplementedError('Plugin must implement create_room()')

    def clone_room(self, old_event_vc_room, link_object):
        """Clone the room, returning a new :class:`VCRoomEventAssociation`.

        :param old_event_vc_room: the original :class:`VCRoomEventAssociation`
        :param link_object: the new object the association will be tied to
        :return: the new :class:`VCRoomEventAssociation`
        """
        return VCRoomEventAssociation(show=old_event_vc_room.show, data=old_event_vc_room.data,
                                      link_object=link_object)

    def can_manage_vc_rooms(self, user, event):
        """Check if a user can manage vc rooms on an event."""
        if self.can_manage_vc(user):
            return True

        if not self.settings.acls.get('acl'):  # everyone has access
            return True
        return self.settings.acls.contains_user('acl', user)

    def can_manage_vc_room(self, user, room):
        """Check if a user can manage a vc room."""
        return (user.is_admin or
                self.can_manage_vc(user) or
                any(evt_assoc.event.can_manage(user) for evt_assoc in room.events))

    def can_manage_vc(self, user):
        """Check if a user has management rights on this VC system."""
        if user.is_admin:
            return True
        return self.settings.acls.contains_user('managers', user)

    def _merge_users(self, target, source, **kwargs):
        self.settings.acls.merge_users(target, source)

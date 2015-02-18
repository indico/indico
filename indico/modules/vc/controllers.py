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

from flask import request, session, redirect, flash
from werkzeug.exceptions import NotFound

from indico.core.db import db
from indico.core.errors import IndicoError
from indico.core.logger import Logger
from indico.modules.vc.models.vc_rooms import VCRoom, VCRoomEventAssociation, VCRoomStatus
from indico.modules.vc.util import get_vc_plugins, get_vc_plugin_by_service_name
from indico.modules.vc.views import WPVCManageEvent
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.web.flask.util import url_for

from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHVCManageEventBase(RHConferenceModifBase):
    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        try:
            self.event_id = int(self._conf.id)
        except ValueError:
            raise IndicoError(_('This page is not available for legacy events.'))
        self.event = self._conf


class RHEventVCRoomMixin:
    def _checkParams(self):
        self.event_vc_room = VCRoomEventAssociation.find_one(event_id=self.event_id,
                                                             vc_room_id=request.view_args['vc_room_id'])
        self.vc_room = self.event_vc_room.vc_room


class RHVCManageEvent(RHVCManageEventBase):
    """Lists the available video conference rooms"""

    def _process(self):
        try:
            vc_rooms = VCRoomEventAssociation.find_for_event(self._conf).all()
        except ValueError:
            raise IndicoError(_('This page is not available for legacy events.'))
        return WPVCManageEvent.render_template('manage_event.html', self._conf, event=self._conf,
                                               event_vc_rooms=vc_rooms, vc_systems=get_vc_plugins().values())


class RHVCManageEventSelectService(RHVCManageEventBase):
    """List available video conference plugins to create a new video room"""

    def _process(self):
        return WPVCManageEvent.render_template('manage_event_select.html', self._conf, event=self._conf,
                                               plugins=get_vc_plugins().values())


class RHVCManageEventCreate(RHVCManageEventBase):
    """Loads the form for the selected VC plugin"""

    def _checkParams(self, params):
        RHVCManageEventBase._checkParams(self, params)
        try:
            self.plugin = get_vc_plugin_by_service_name(request.view_args['service'])
        except KeyError:
            raise NotFound

    def _process(self):
        if not self.plugin.can_manage_vc_rooms(session.user, self.event):
            flash(_('You are not allowed to create VC rooms for this event.'), 'error')
            return redirect(url_for('.manage_vc_rooms', self.event))

        form = self.plugin.create_form(event=self.event)

        if form.validate_on_submit():
            data = form.data

            vc_room = VCRoom(created_by_user=session.user)
            vc_room.type = self.plugin.service_name
            vc_room.status = VCRoomStatus.created
            vc_room.name = data.pop('name')
            vc_room.data = data

            event_vc_room = VCRoomEventAssociation(event_id=self.event_id, vc_room=vc_room)

            db.session.add_all((vc_room, event_vc_room))

            # TODO: API
            # create_room(vc_room)
            # notify_created(vc_room, self.event, session.user)

            flash(_('Video conference room created'), 'success')
            return redirect(url_for('.manage_vc_rooms', self.event))
        form_html = self.plugin.render_form(plugin=self.plugin, event=self.event, form=form)

        return WPVCManageEvent.render_string(form_html, self.event)


class RHVCSystemEventBase(RHEventVCRoomMixin, RHVCManageEventBase):

    def _checkParams(self, params):
        RHVCManageEventBase._checkParams(self, params)
        RHEventVCRoomMixin._checkParams(self)
        try:
            self.plugin = get_vc_plugin_by_service_name(request.view_args['service'])
        except KeyError:
            raise NotFound


class RHVCManageEventModify(RHVCSystemEventBase):
    """Modifies an existing VC room"""

    def _process(self):
        if not self.plugin.can_manage_vc_rooms(session.user, self.event):
            flash(_('You are not allowed to modify VC rooms for this event.'), 'error')
            return redirect(url_for('.manage_vc_rooms', self.event))

        form = self.plugin.create_form(event=self.event, existing_vc_room=self.vc_room)

        if form.validate_on_submit():
            # form.data is a generated property, so we cannot just .pop() directly from it
            data = form.data
            self.vc_room.name = data.pop('name')
            self.vc_room.data = data
            self.vc_room.modified_dt = now_utc()

            # TODO: API
            # If the attributes have changed, update the booking
            # if attrs_changed(self.vc_room, 'name', 'description', ...):
            #     update_room(self.vc_room)
            # notify_modified(self.vc_room, self.event, session.user)

            flash(_('Video conference room updated'), 'success')
            return redirect(url_for('.manage_vc_rooms', self.event))

        form_html = self.plugin.render_form(plugin=self.plugin, event=self.event, form=form,
                                            existing_vc_room=self.vc_room)

        return WPVCManageEvent.render_string(form_html, self.event)


class RHVCManageEventRemove(RHVCSystemEventBase):
    """Removes an existing VC room"""

    def _process(self):
        if not self.plugin.can_manage_vc_rooms(session.user, self.event):
            flash(_('You are not allowed to remove VC rooms from this event.'), 'error')
            return redirect(url_for('.manage_vc_rooms', self.event))

        Logger.get('modules.vc').info("Detaching VC room {} from event {}".format(
            self.vc_room, self._conf))
        db.session.delete(self.event_vc_room)

        # delete room if not connected to any other events
        if not self.vc_room.events:
            Logger.get('modules.vc').info("Deleting VC room {}".format(self.vc_room))
            db.session.delete(self.vc_room)
            # TODO: VC-specific code !!!!
        flash(_("Video conference room '{0}' has been removed").format(self.vc_room.name), 'success')
        return redirect(url_for('.manage_vc_rooms', self.event))

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

import transaction
from collections import defaultdict
from flask import request, session, redirect, flash, json, Response
from sqlalchemy import func
from werkzeug.exceptions import NotFound, BadRequest

from indico.core.db import db
from indico.core.errors import IndicoError
from indico.core.logger import Logger
from indico.modules.vc.exceptions import VCRoomError, VCRoomNotFoundError
from indico.modules.vc.models.vc_rooms import VCRoom, VCRoomEventAssociation, VCRoomStatus, VCRoomLinkType
from indico.modules.vc.notifications import notify_created
from indico.modules.vc.util import get_vc_plugins, resolve_title
from indico.modules.vc.views import WPVCManageEvent, WPVCEventPage
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.web.flask.util import url_for, redirect_or_jsonify
from indico.web.forms.base import FormDefaults

from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


def process_vc_room_association(plugin, event, vc_room, form, event_vc_room=None):
    # disable autoflush, so that the new event_vc_room does not
    # influence the result
    with db.session.no_autoflush:
        if event_vc_room is None:
            event_vc_room = VCRoomEventAssociation()

        plugin.handle_form_data_association(event, vc_room, event_vc_room, form.data)

        num_existing = VCRoomEventAssociation.find(
            VCRoom.type == plugin.service_name,
            event_id=event.id,
            link_type=event_vc_room.link_type,
            link_id=event_vc_room.link_id
        ).join(VCRoom).count()

    if event_vc_room.link_type != VCRoomLinkType.event and num_existing > 0:
        transaction.abort()
        flash(_("There is already a {0} room attached to '{1}'!").format(
            plugin.service_name, resolve_title(event_vc_room.link_object)), 'error')

        return None
    else:
        return event_vc_room


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
        self.event_vc_room = VCRoomEventAssociation.find_one(id=request.view_args['event_vc_room_id'])
        self.vc_room = self.event_vc_room.vc_room


class RHVCManageEvent(RHVCManageEventBase):
    """Lists the available video conference rooms"""

    def _process(self):
        try:
            vc_rooms = VCRoomEventAssociation.find_for_event(self._conf, include_hidden=True).all()
        except ValueError:
            raise IndicoError(_('This page is not available for legacy events.'))
        return WPVCManageEvent.render_template('manage_event.html', self._conf, event=self._conf,
                                               event_vc_rooms=vc_rooms, plugins=get_vc_plugins().values())


class RHVCManageEventSelectService(RHVCManageEventBase):
    """List available video conference plugins to create a new video room"""

    def _process(self):
        return WPVCManageEvent.render_template('manage_event_select.html', self._conf, event=self._conf,
                                               plugins=get_vc_plugins().values())


class RHVCManageEventCreateBase(RHVCManageEventBase):
    def _checkParams(self, params):
        RHVCManageEventBase._checkParams(self, params)
        try:
            self.plugin = get_vc_plugins().get(request.view_args['service'])
        except KeyError:
            raise NotFound


class RHVCManageEventCreate(RHVCManageEventCreateBase):
    """Loads the form for the selected VC plugin"""

    def _process(self):
        if not self.plugin.can_manage_vc_rooms(session.user, self.event):
            flash(_('You are not allowed to create VC rooms for this event.'), 'error')
            return redirect(url_for('.manage_vc_rooms', self.event))

        form = self.plugin.create_form(event=self.event)

        if form.validate_on_submit():
            vc_room = VCRoom(created_by_user=session.user)
            vc_room.type = self.plugin.service_name
            vc_room.status = VCRoomStatus.created

            event_vc_room = process_vc_room_association(self.plugin, self.event, vc_room, form)
            if not event_vc_room:
                return redirect(url_for('.manage_vc_rooms', self.event))

            self.plugin.handle_form_data_vc_room(vc_room, form.data)

            try:
                self.plugin.create_room(vc_room, self.event)
                notify_created(self.plugin, vc_room, event_vc_room, self.event, session.user)
            except VCRoomError as err:
                if err.field is None:
                    raise
                field = getattr(form, err.field)
                field.errors.append(err.message)
            else:
                db.session.add_all((vc_room, event_vc_room))
                # TODO: notify_created(vc_room, self.event, session.user)

                flash(_('Video conference room created'), 'success')
                return redirect(url_for('.manage_vc_rooms', self.event))

        form_html = self.plugin.render_form(plugin=self.plugin, event=self.event, form=form,
                                            skip_fields=form.skip_fields | {'name'})

        return WPVCManageEvent.render_string(form_html, self.event)


class RHVCSystemEventBase(RHEventVCRoomMixin, RHVCManageEventBase):

    def _checkParams(self, params):
        RHVCManageEventBase._checkParams(self, params)
        RHEventVCRoomMixin._checkParams(self)
        try:
            self.plugin = get_vc_plugins().get(request.view_args['service'])
        except KeyError:
            raise NotFound


class RHVCManageEventModify(RHVCSystemEventBase):
    """Modifies an existing VC room"""

    def _process(self):
        if not self.plugin.can_manage_vc_rooms(session.user, self.event):
            flash(_('You are not allowed to modify VC rooms for this event.'), 'error')
            return redirect(url_for('.manage_vc_rooms', self.event))

        form = self.plugin.create_form(self.event,
                                       existing_vc_room=self.vc_room,
                                       existing_event_vc_room=self.event_vc_room)

        if form.validate_on_submit():

            self.plugin.handle_form_data_vc_room(self.vc_room, form.data)

            event_vc_room = process_vc_room_association(
                self.plugin, self.event, self.vc_room, form, event_vc_room=self.event_vc_room)
            if not event_vc_room:
                return redirect(url_for('.manage_vc_rooms', self.event))

            self.vc_room.modified_dt = now_utc()

            try:
                self.plugin.update_room(self.vc_room, self.event)
            except VCRoomNotFoundError as err:
                Logger.get('modules.vc').warning("VC room {} not found. Setting it as deleted.".format(self.vc_room))
                self.vc_room.status = VCRoomStatus.deleted
                flash(err.message, 'error')
                return redirect(url_for('.manage_vc_rooms', self.event))
            except VCRoomError as err:
                if err.field is None:
                    raise
                field = getattr(form, err.field)
                field.errors.append(err.message)
                transaction.abort()
            else:
                # TODO
                # notify_modified(self.vc_room, self.event, session.user)

                flash(_('Video conference room updated'), 'success')
                return redirect(url_for('.manage_vc_rooms', self.event))

        form_html = self.plugin.render_form(plugin=self.plugin, event=self.event, form=form,
                                            existing_vc_room=self.vc_room)

        return WPVCManageEvent.render_string(form_html, self.event)


class RHVCManageEventRefresh(RHVCSystemEventBase):
    """Refreshes an existing VC room, fetching information from the VC system"""

    def _process(self):
        if not self.plugin.can_manage_vc_rooms(session.user, self.event):
            flash(_('You are not allowed to refresh VC rooms in this event.'), 'error')
            return redirect(url_for('.manage_vc_rooms', self.event))

        Logger.get('modules.vc').info("Refreshing VC room {} from event {}".format(self.vc_room, self._conf))

        try:
            self.plugin.refresh_room(self.vc_room, self.event)
        except VCRoomNotFoundError as err:
            Logger.get('modules.vc').warning("VC room {} not found. Setting it as deleted.".format(self.vc_room))
            self.vc_room.status = VCRoomStatus.deleted
            flash(err.message, 'error')
            return redirect(url_for('.manage_vc_rooms', self.event))

        flash(_("Video conference room '{0}' has been refreshed").format(self.vc_room.name), 'success')
        return redirect(url_for('.manage_vc_rooms', self.event))


class RHVCManageEventRemove(RHVCSystemEventBase):
    """Removes an existing VC room"""

    def _process(self):
        if not self.plugin.can_manage_vc_rooms(session.user, self.event):
            flash(_('You are not allowed to remove VC rooms from this event.'), 'error')
            return redirect(url_for('.manage_vc_rooms', self.event))

        Logger.get('modules.vc').info("Detaching VC room {} from event {} ({})".format(
                                      self.vc_room, self.event_vc_room.event, self.event_vc_room.link_object))

        db.session.delete(self.event_vc_room)
        db.session.flush()

        # delete room if not connected to any other events
        if not self.vc_room.events:
            Logger.get('modules.vc').info("Deleting VC room {}".format(self.vc_room))
            if self.vc_room.status != VCRoomStatus.deleted:
                self.plugin.delete_room(self.vc_room, self.event)
            db.session.delete(self.vc_room)

        flash(_("Video conference room '{0}' has been removed").format(self.vc_room.name), 'success')
        return redirect(url_for('.manage_vc_rooms', self.event))


class RHVCEventPage(RHConferenceBaseDisplay):
    """Lists the VC rooms in an event page"""

    def _process(self):
        event_vc_rooms = VCRoomEventAssociation.find_for_event(self._conf).all()
        vc_plugins_available = True if get_vc_plugins() else False
        linked_to = defaultdict(lambda: defaultdict(list))
        for event_vc_room in event_vc_rooms:
            linked_to[event_vc_room.link_type.name][event_vc_room.link_object].append(event_vc_room)
        return WPVCEventPage.render_template('event_vc.html', self._conf, event=self._conf,
                                             event_vc_rooms=event_vc_rooms, linked_to=linked_to,
                                             vc_plugins_available=vc_plugins_available)


class RHVCManageAttach(RHVCManageEventCreateBase):
    """Attaches a room to the event"""

    def _process(self):
        defaults = FormDefaults(self.plugin.get_vc_room_attach_form_defaults(self.event))
        form = self.plugin.vc_room_attach_form(prefix='vc-', obj=defaults, event=self.event,
                                               service=self.plugin.service_name)

        if form.validate_on_submit():
            vc_room = form.data['room']
            if not self.plugin.can_manage_vc_rooms(session.user, self.event):
                flash(_("You are not allowed to attach '{}' rooms to this event.").format(self.plugin.service_name),
                      'error')
            else:
                event_vc_room = process_vc_room_association(self.plugin, self.event, vc_room, form)
                if event_vc_room:
                    flash(_("The room has been attached to the event."), 'success')
                    db.session.add(event_vc_room)
            return redirect_or_jsonify(url_for('.manage_vc_rooms', self.event), flash=False)

        return WPVCManageEvent.render_template('attach_room.html', self._conf, event=self._conf, form=form,
                                               skip_fields=form.conditional_fields | {'room'})


class RHVCManageSearch(RHVCManageEventCreateBase):
    """Searches for a room based on its name"""

    def _checkParams(self, params):
        RHVCManageEventCreateBase._checkParams(self, params)

        self.query = request.args.get('q', '')
        if (len(self.query) < 3):
            raise BadRequest("A query has to be provided, with at least 3 characters")

    def _iter_allowed_rooms(self):
        query = (db.session.query(VCRoom, func.count(VCRoomEventAssociation.id).label('event_count'))
                 .options(db.lazyload('vidyo_extension'))
                 .filter(func.lower(VCRoom.name).contains(self.query.lower()), VCRoom.status != VCRoomStatus.deleted,
                         VCRoom.type == self.plugin.service_name)
                 .join(VCRoomEventAssociation)
                 .group_by(VCRoom.id)
                 .order_by(db.desc('event_count'))
                 .limit(10))

        return ((room, count) for room, count in query
                if room.plugin.can_manage_room(session.user, room))

    def _process(self):
        return Response(json.dumps([{'id': room.id, 'name': room.name, 'count': count}
                                   for room, count in self._iter_allowed_rooms()]),  mimetype='application/json')

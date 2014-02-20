# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.

from flask import request, session

from MaKaC.webinterface import urlHandlers as UH

from indico.core.db import db
from indico.core.errors import NotFoundError
from indico.util.i18n import _

from . import RHRoomBookingAdminBase
from ..decorators import requires_location
from ...models.room_bookable_times import BookableTime
from ...models.room_nonbookable_dates import NonBookableDate
from ...models.rooms import Room
from ...models.photos import Photo
from ...views.admin import rooms as room_views

class CandidateDataFrom(object):
    DEFAULTS, PARAMS, SESSION = range(3)


class RHRoomBookingDeleteRoom(RHRoomBookingAdminBase):

    def _checkParams(self):
        self._room = Room.getRoomById(request.form.get('roomID', type=int))
        self._target = self._room

    def _process(self):
        # Check whether deletion is possible
        if self._room.doesHaveLiveReservations():
            # Impossible
            session['rbDeletionFailed'] = True
            self._redirect(UH.UHRoomBookingRoomDetails.getURL(self._room))  # room details
        else:
            # Possible - delete
            Room.removeRoom(self._room)
            session['rbTitle'] = _('Room has been deleted.')
            session['rbDescription'] = _('You have successfully deleted the room. '
                                         'All its archival, cancelled and rejected '
                                         'bookings have also been deleted.')
            self._redirect(UH.UHRoomBookingStatement.getURL())  # deletion confirmation


class RHRoomBookingRoomForm(RHRoomBookingAdminBase):
    """
    Form for creating NEW and MODIFICATION of an existing room.
    """

    @requires_location(parameter_name='roomLocation', request_attribute='view_args')
    def _checkParams(self):
        self._new = 'roomID' not in request.view_args
        self._room = session.pop('_rbRoom', None)
        self._equipments = session.pop('_rbRoomEquipments', [])
        if self._equipments:
            self._equipments = [eq.id for eq in self._equipments]
        self._bookable_times = session.pop('_rbBookableTimes',
                                           [BookableTime(start_time=None, end_time=None)])
        self._nonbookable_dates = session.pop('_rbNonBookableDates',
                                              [NonBookableDate(start_date=None, end_date=None)])
        if not self._room:
            if self._new:
                self._room = Room.getRoomWithDefaults()
            else:
                self._room = Room.getRoomById(int(request.view_args.get('roomID')))
                self._equipments = self._room.getEquipmentIds()
                self._bookable_times = self._room.getBookableTimes()
                self._nonbookable_dates = self._room.getNonBookableDates()
        self._errors = session.pop('_rbErrors', [])

    def _process(self):
        return room_views.WPRoomBookingRoomForm(self).display()


class RHRoomBookingSaveRoom(RHRoomBookingAdminBase):
    """
    Performs physical INSERT or UPDATE.
    When succeeded redirects to room details, otherwise returns to room form.
    """

    def _uploadPhotos(self, candRoom, params):
        self._room.addPhoto(
            Photo(
                large_content=request.files.get('largePhotoPath'),
                small_content=request.files.get('smallPhotoPath')
            )
        )

    @requires_location('roomLocation')
    def _checkParams(self):
        roomId = request.form.get('roomID', type=int)
        if roomId:
            self._room = Room.getRoomById(roomId)
            if not self._room:
                raise NotFoundError(_('There is no room with id: {0}').format(roomId))
        else:
            self._room = Room.getRoomWithDefaults()
        self._errors = self._checkAndSetParams()
        self._target = self._room

    def _process(self):
        if self._errors:
            session['_rbErrors'] = self._errors
            session['_rbRoom'] = self._room
            session['_rbRoomEquipments'] = self._equipments
            session['_rbBookableTimes'] = self._bookable_times
            session['_rbNonBookableDates'] = self._nonbookable_dates
            self._redirect(UH.UHRoomBookingRoomForm.getURL(roomLocation=self._location.name))
        else:
            # Succeeded
            self._room.setEquipments(self._equipments)
            self._room.setBookableTimes(self._bookable_times)
            self._room.setNonBookableDates(self._nonbookable_dates)
            if self._room.id:
                db.session.add(self._room)
                self._room.notifyAboutResponsibility()
                url = UH.UHRoomBookingRoomDetails.getURL(self._room)
            else:
                self._location.addRoom(self._room)
                db.session.add(self._location)
                self._room.notifyAboutResponsibility()
                url = UH.UHRoomBookingAdminLocation.getURL(self._location, actionSucceeded=True)
            self._redirect(url)

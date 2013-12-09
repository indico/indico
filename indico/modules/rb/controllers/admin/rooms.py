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

from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.pages import admins as adminPages
from indico.core.logger import Logger

from indico.core.db import db
from indico.modules.rb.controllers.admin import RHRoomBookingAdminBase
from indico.modules.rb.controllers.utils import FormMode
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.rooms import Room


logger = Logger.get('requestHandler')


class RHRoomBookingDeleteRoom(RHRoomBookingAdminBase):

    def _checkParams(self):
        self._room = Room.getRoomById(request.form.get('roomID', type=int))
        self._target = self._room

    def _process(self):
        # Check whether deletion is possible
        if self._room.doesHaveLiveReservations():
            # Impossible
            session['rbDeletionFailed'] = True
            self._redirect(urlHandlers.UHRoomBookingRoomDetails.getURL(room))  # room details
        else:
            # Possible - delete
            try:
                db.session.delete(self._room)
                db.session.commit()
            except:
                db.session.rollback()
                # TODO: raise
            session['rbTitle'] = _("Room has been deleted.")
            session['rbDescription'] = _("You have successfully deleted the room. "
                                         "All its archival, cancelled and rejected "
                                         "bookings have also been deleted.")
            self._redirect(urlHandlers.UHRoomBookingStatement.getURL())  # deletion confirmation


# TODO
class RHRoomBookingRoomForm(RHRoomBookingAdminBase):
    """
    Form for creating NEW and MODIFICATION of an existing room.
    """

    def _checkParams( self, params ):
        # DATA FROM?
        self._dataFrom = CandidateDataFrom.DEFAULTS
        if params.get( "candDataInParams" ):
            self._dataFrom = CandidateDataFrom.PARAMS
        if session.get('rbCandDataInSession'):
            self._dataFrom = CandidateDataFrom.SESSION

        # Room ID?
        roomID = None
        roomLocation = None
        if self._dataFrom == CandidateDataFrom.SESSION:
            roomID = session.get('rbRoomID')
            roomLocation = session.get('rbRoomLocation')
        else:
            roomID = params.get( "roomID" )
            roomLocation = params.get( "roomLocation" )
        if roomID: roomID = int( roomID )

        # FORM MODE?
        if roomID:
            self._formMode = FormMode.MODIF
        else:
            self._formMode = FormMode.NEW

        # SHOW ERRORS?
        self._showErrors = session.get('rbShowErrors')
        if self._showErrors:
            self._errors = session.get('rbErrors')

        # CREATE CANDIDATE OBJECT
        candRoom = None
        if self._formMode == FormMode.NEW:
            locationName = params.get("roomLocation", "")
            location = Location.parse(locationName)
            if str(location) == "None":
                # Room should be inserted into default backend => using Factory
                candRoom = Factory.newRoom()
            else:
                candRoom = location.newRoom()
            if self._dataFrom == CandidateDataFrom.SESSION:
                self._loadRoomCandidateFromSession( candRoom )
            else:
                self._loadRoomCandidateFromDefaults( candRoom )

        if self._formMode == FormMode.MODIF:
            candRoom = CrossLocationQueries.getRooms( roomID = roomID, location = roomLocation )

            if self._dataFrom == CandidateDataFrom.PARAMS:
                self._loadRoomCandidateFromParams( candRoom, params )
            if self._dataFrom == CandidateDataFrom.SESSION:
                self._loadRoomCandidateFromSession( candRoom )

        self._errors = session.get('rbErrors')

        # After searching for responsible
        if params.get( 'selectedPrincipals' ):
            candRoom.responsibleId = params['selectedPrincipals']

        self._candRoom = self._target = candRoom
        self._clearSessionState()

    def _process(self):
        return adminPages.WPRoomBookingRoomForm(self).display()


class RHRoomBookingSaveRoom(RHRoomBookingAdminBase):
    """
    Performs physical INSERT or UPDATE.
    When succeeded redirects to room details, otherwise returns to room form.
    """

    def _uploadPhotos( self, candRoom, params ):
        if (params.get( "largePhotoPath" ) and params.get( "smallPhotoPath" )
            and params["largePhotoPath"].filename and params["smallPhotoPath"].filename):
            candRoom.savePhoto( params["largePhotoPath"] )
            candRoom.saveSmallPhoto( params["smallPhotoPath"] )

    def _checkParams(self):
        roomID = request.form.get('roomID')
        roomLocation = request.form.get('roomLocation')

        candRoom = None
        if roomID:
            self._formMode = FormMode.MODIF
            candRoom = Room.getRoomById(int(roomID))
        else:
            self._formMode = FormMode.NEW
            if roomLocation:
                location = Location.getLocationByName(roomLocation)
            else:
                location = Location.getDefaultLocation()
            room = Room('')  # name is required
            location.addRoom(room)

        self._loadRoomCandidateFromParams(candRoom, request.form)
        self._candRoom = self._target = candRoom

    def _process(self):
        candRoom = self._candRoom

        errors = self._getErrorsOfRoomCandidate(candRoom)
        if errors:
            # Failed
            session['rbActionSucceeded'] = False
            session['rbCandDataInSession'] = True
            session['rbErrors'] = errors
            session['rbShowErrors'] = True

            self._saveRoomCandidateToSession(candRoom)
            url = urlHandlers.UHRoomBookingRoomForm.getURL(roomLocation=candRoom.location.name)
            self._redirect(url) # Redirect again to FORM
        else:
            # Succeeded
            if self._formMode == FormMode.MODIF:
                try:
                    db.session.add(candRoom)
                    db.session.commit()
                except:
                    db.session.rollback()
                    # TODO: raise
                # if responsibleId changed
                candRoom.notifyAboutResponsibility()
                url = urlHandlers.UHRoomBookingRoomDetails.getURL(candRoom)
            elif self._formMode == FormMode.NEW:
                try:
                    db.session.add_all([candRoom.location, candRoom])
                    db.session.commit()
                except:
                    db.session.rollback()
                    # TODO: raise
                candRoom.notifyAboutResponsibility()
                url = urlHandlers.UHRoomBookingAdminLocation.getURL(candRoom.locationName, actionSucceeded=True)

            self._uploadPhotos(candRoom, request.form)
            session['rbActionSucceeded'] = True
            session['rbFormMode'] = self._formMode
            self._redirect(url)  # room details

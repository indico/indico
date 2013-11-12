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


class RHRoomBookingDeleteRoom( RHRoomBookingAdminBase ):

    def _checkParams( self , params ):
        roomID = params.get( "roomID" )
        roomID = int( roomID )
        roomLocation = params.get( "roomLocation" )
        self._room = CrossLocationQueries.getRooms( roomID = roomID, location = roomLocation )
        self._target = self._room

    def _process( self ):
        room = self._room
        # Check whether deletion is possible
        liveResv = room.getLiveReservations()
        if len( liveResv ) == 0:
            # Possible - delete
            for resv in room.getReservations():
                resv.remove()
            room.remove()
            session['rbTitle'] = _("Room has been deleted.")
            session['rbDescription'] = _("You have successfully deleted the room. All its archival, cancelled and rejected bookings have also been deleted.")
            url = urlHandlers.UHRoomBookingStatement.getURL()
            self._redirect( url ) # Redirect to deletion confirmation
        else:
            # Impossible
            session['rbDeletionFailed'] = True
            url = urlHandlers.UHRoomBookingRoomDetails.getURL( room )
            self._redirect( url ) # Redirect to room DETAILS


class RHRoomBookingRoomForm( RHRoomBookingAdminBase ):
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

    def _process( self ):
        p = admins.WPRoomBookingRoomForm( self )
        return p.display()


class RHRoomBookingSaveRoom( RHRoomBookingAdminBase ):
    """
    Performs physical INSERT or UPDATE.
    When succeeded redirects to room details, otherwise returns to room form.
    """

    def _uploadPhotos( self, candRoom, params ):
        if (params.get( "largePhotoPath" ) and params.get( "smallPhotoPath" )
            and params["largePhotoPath"].filename and params["smallPhotoPath"].filename):
            candRoom.savePhoto( params["largePhotoPath"] )
            candRoom.saveSmallPhoto( params["smallPhotoPath"] )

    def _checkParams( self, params ):

        roomID = params.get( "roomID" )
        roomLocation = params.get( "roomLocation" )

        candRoom = None
        if roomID:
            self._formMode = FormMode.MODIF
            if roomID: roomID = int( roomID )
            candRoom = CrossLocationQueries.getRooms( roomID = roomID, location = roomLocation )
        else:
            self._formMode = FormMode.NEW
            if roomLocation:
                name = Location.parse(roomLocation).friendlyName
            else:
                name = Location.getDefaultLocation().friendlyName
            location = Location.parse(name)
            candRoom = location.newRoom()
            candRoom.locationName = name

        self._loadRoomCandidateFromParams( candRoom, params )
        self._candRoom = self._target = candRoom
        self._params = params

    def _process( self ):
        candRoom = self._candRoom
        params = self._params

        errors = self._getErrorsOfRoomCandidate( candRoom )
        if not errors:
            # Succeeded
            if self._formMode == FormMode.MODIF:
                candRoom.update()
                # if responsibleId changed
                candRoom.notifyAboutResponsibility()
                url = urlHandlers.UHRoomBookingRoomDetails.getURL(candRoom)

            elif self._formMode == FormMode.NEW:
                candRoom.insert()
                candRoom.notifyAboutResponsibility()
                url = urlHandlers.UHRoomBookingAdminLocation.getURL(Location.parse(candRoom.locationName), actionSucceeded = True)

            self._uploadPhotos(candRoom, params)
            session['rbActionSucceeded'] = True
            session['rbFormMode'] = self._formMode
            self._redirect(url) # Redirect to room DETAILS
        else:
            # Failed
            session['rbActionSucceeded'] = False
            session['rbCandDataInSession'] = True
            session['rbErrors'] = errors
            session['rbShowErrors'] = True

            self._saveRoomCandidateToSession( candRoom )
            url = urlHandlers.UHRoomBookingRoomForm.getURL(roomLocation=candRoom.locationName)
            self._redirect( url ) # Redirect again to FORM

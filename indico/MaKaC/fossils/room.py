# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from MaKaC.common.fossilize import IFossil

# is this used anywhere?!
class IRoomMapFossil(IFossil):

    def id(self):
        """ Room ID """

    def name(self):
        """ Room name """

    def locationName(self):
        """ Room location """

    def floor(self):
        """ Room floor """

    def roomNr(self):
        """ Room number """

    def capacity(self):
        """ Room capacity """

    def comments(self):
        """ Room comments """

    def responsibleId(self):
        """ ID of the responsible person for the room """

    def getTipPhotoURL(self):
        """ URL of the tip photo of the room """

    def isActive(self):
        """ Is the room active? """

    def isReservable(self):
        """ Is the room public? """

    def getIsAutoConfirm(self):
        """ Has the room auto-confirmation of schedule? """

    def getBookingUrl(self):
        """ Room booking URL """

    def getDetailsUrl(self):
        """ Room details URL """

    def getMarkerDescription(self):
        """ Room description for the map marker """

    def needsAVCSetup(self):
        """ Setup for audio and video conference """

    def hasWebcastRecording(self):
        """ Setup for webcast/recording """

    def getAvailableVC(self):
        """ Available equipment for audio and video conference """

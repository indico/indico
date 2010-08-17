# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from MaKaC.common.fossilize import IFossil

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

    def getUrl(self):
        """ Room URL """

    def getMarkerDescription(self):
        """ Room description for the map marker """

    def needsAVCSetup(self):
        """ Setup for for audio and video conference """

    def getAvailableVC(self):
        """ Available equipment for audio and video conference """

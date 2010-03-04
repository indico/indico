# -*- coding: utf-8 -*-
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

class IAvatarMinimalFossil(IFossil):

    def getId(self):
        """ Avatar id"""

    def getStraightFullName(self):
        """ Avatar full name, the one usually displayed """
    getStraightFullName.name = "name"

    def getEmail( self ):
        """ Avatar email """


class IAvatarDetailedFossil(IAvatarMinimalFossil):

    def getFirstName(self):
        """ Avatar first name """

    def getFamilyName(self):
        """ Avatar family name """

    def getTitle( self ):
        """ Avatar name title (Mr, Mrs..) """

    def getOrganisation( self ):
        """ Avatar organisation / affiliation """
    getOrganisation.name = "affiliation"


class IAvatarAllDetailsFossil(IAvatarDetailedFossil):

    def getAddress( self ):
        """ Avatar address """

    def getTelephone( self ):
        """ Avatar telephone """

    def getFax(self):
        """ Avatar fax """

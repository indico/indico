# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from indico.legacy.common.fossilize import IFossil


class IGroupFossil(IFossil):

    def getId(self):
        """ Group id """

    def getName(self):
        """ Group name """

    def getEmail(self):
        """ Group email """

    def getProvider(self):
        pass
    getProvider.produce = lambda x: getattr(x, 'provider', None)

    def getIdentifier(self):
        pass
    getIdentifier.produce = lambda x: 'Group:{}:{}'.format(getattr(x, 'provider', ''), x.id)


class IAvatarMinimalFossil(IFossil):

    def getId(self):
        """ Avatar id"""

    def getIdentifier(self):
        pass
    getIdentifier.produce = lambda x: 'User:{}'.format(x.id)

    def getStraightFullName(self):
        """ Avatar full name, the one usually displayed """
    getStraightFullName.name = "name"
    getStraightFullName.produce = lambda x: x.getStraightFullName(upper=False)


class IAvatarFossil(IAvatarMinimalFossil):

    def getEmail( self ):
        """ Avatar email """

    def getFirstName(self):
        """ Avatar first name """

    def getFamilyName(self):
        """ Avatar family name """

    def getTitle( self ):
        """ Avatar name title (Mr, Mrs..) """

    def getTelephone( self ):
        """ Avatar telephone """
    getTelephone.name = "phone"

    def getOrganisation( self ):
        """ Avatar organisation / affiliation """
    getOrganisation.name = "affiliation"

    def getFax(self):
        """ Avatar fax """

    def getAddress( self ):
        """ Avatar address """

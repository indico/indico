# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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

from ZODB import FileStorage, DB
from ZODB.DB import DB, transaction
from ZODB.PersistentMapping import PersistentMapping
from persistent import Persistent

from MaKaC.plugins.RoomBooking.default.factory import Factory
from MaKaC.rb_customAttributesManager import CustomAttributesManagerBase
from MaKaC.rb_location import Location

# Branch name in ZODB root
_CUSTOM_ATTRIBUTES_LIST = 'CustomAttributesList' # DICTIONARY of lists; indexed by location name

class CustomAttributesManager( CustomAttributesManagerBase ):
    """ ZODB specific implementation """

    @staticmethod
    def supportsAttributeManagement( *args, **kwargs ):
        location = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )

        # CERN uses generic ZODB-based plugin which DOES allow
        # dynamic room attributes management.
        # However, CERN-specific needs require to turn off this
        # feature, because rooms are managed centrally, and we
        # just import them.
        #if location == "CERN":
        #    return False

        return True

    @staticmethod
    def getRoot():
        return Factory.getDALManager().getRoot(_CUSTOM_ATTRIBUTES_LIST)

    @staticmethod
    def getAttributes( *args, **kwargs ):
        location = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )

        root = CustomAttributesManager.getRoot()

        if not root.has_key( location ):
            CustomAttributesManager.setAttributes( [], location = location )

        return CustomAttributesManager.getRoot()[location]

    @staticmethod
    def setAttributes( attsList, *args, **kwargs  ):
        location = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )

        for at in attsList:
            errors = CustomAttributesManagerBase.checkAttribute( at )
            if errors: raise str( errors )

        dic = CustomAttributesManager.getRoot()
        dic[location] = attsList
        root = Factory.getDALManager().getRoot()
        root[_CUSTOM_ATTRIBUTES_LIST] = dic

    @staticmethod
    def insertAttribute( customAttribute, *args, **kwargs ):
        """ Adds new attribute to the list of custom attributes."""
        location = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )

        errors = []
        errors = CustomAttributesManagerBase.checkAttribute( customAttribute )
        if errors: raise str( errors )

        attsList = CustomAttributesManager.getAttributes( location = location )
        attsList.append( customAttribute )
        CustomAttributesManager.setAttributes( attsList, location = location )

    @staticmethod
    def removeAttribute( customAttributeName, *args, **kwargs ):
        """ Deletes attribute from the list of custom attributes. """
        location = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )

        attsList = CustomAttributesManager.getAttributes( location = location )
        for at in attsList:
            if at['name'] == customAttributeName:
                attsList.remove( at )
                break;
        CustomAttributesManager.setAttributes( attsList, location = location )

    @staticmethod
    def setRequired( customAttributeName, isRequired, *args, **kwargs ):
        """ Makes attribute required."""
        location = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )

        attsList = CustomAttributesManager.getAttributes( location = location )
        for at in attsList:
            if at['name'] == customAttributeName:
                at['required'] = isRequired
                break;
        CustomAttributesManager.setAttributes( attsList, location = location )

    @staticmethod
    def setHidden( customAttributeName, isHidden, *args, **kwargs ):
        """ Makes attribute hidden."""
        location = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )

        attsList = CustomAttributesManager.getAttributes( location = location )
        for at in attsList:
            if at['name'] == customAttributeName:
                at['hidden'] = isHidden
                break;
        CustomAttributesManager.setAttributes( attsList, location = location )

if __name__ == '__main__':
    pass

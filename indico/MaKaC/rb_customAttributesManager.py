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

"""
Part of Room Booking Module (rb_)
Responsible: Piotr Wlodarek
"""

class CustomAttributesManagerBase:
    """
    Generic manager for room attributes that are plugin-specific.

    It manages the list of rooms' possible attributes.
    The list does NOT include core attributes (like id,
    room number etc.) This is only to manage plugin-specific
    attributes, called _Custom_Attributes_.

    All attributes are strings.

    The list of possible equipment is defined either
    programmatically in CustomAttributesManagerLOCATION
    implementation or by the Room Booking admin
    (if plugin permits).

    This list is used mainly for generating user web interface.
    """

    @staticmethod
    def supportsAttributeManagement( *args, **kwargs ):
        """
        Returns True if plugin supports adding and
        removing room attributes (modyfing 'room shema').
        Otherwise returns False.
        """
        return False

    @staticmethod
    def getAttributes( *args, **kwargs ):
        """ Returns the List of rooms' possible equipment. """
        pass

    @staticmethod
    def setAttributes( customAttributeList, *args, **kwargs ):
        """ Sets the List of rooms' custom attributes. """
        raise NotImplementedError('This plugin does not support modyfing the list of room attributes')

    @staticmethod
    def insertAttribute( customAttribute, *args, **kwargs ):
        """ Adds new attribute to the list of custom attributes."""
        raise NotImplementedError('This plugin does not support modyfing the list of room attributes')

    @staticmethod
    def removeAttribute( customAttributeName, *args, **kwargs ):
        """ Deletes attribute from the list of custom attributes. """
        raise NotImplementedError('This plugin does not support modyfing the list of room attributes')

    @staticmethod
    def setRequired( customAttributeName, isRequired, *args, **kwargs ):
        """ Sets the 'required' attribute of the custom attribute. """
        raise NotImplementedError('This plugin does not support modyfing the list of room attributes')

    @staticmethod
    def setHidden( customAttributeName, isHidden, *args, **kwargs ):
        """ Sets the 'hidden' attribute of the custom attribute. """
        raise NotImplementedError('This plugin does not support modyfing the list of room attributes')

    @staticmethod
    def checkAttribute( at ):
        """
        Checks whether custom attribute is proper dictionary.
        """
        if not isinstance( at, dict ): return 'CustomAttribute must be a dictionary'
        if not at.has_key( 'name' ): return 'CustomAttribute dictionary must have a name key'
        if not at.has_key( 'type' ): return 'CustomAttribute dictionary must have a type key'
        if not at.has_key( 'required' ): return 'CustomAttribute dictionary must have a required key'
        return ''

if __name__ == '__main__':
    pass

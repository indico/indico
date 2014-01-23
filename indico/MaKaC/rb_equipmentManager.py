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


class EquipmentManagerBase:
    """
    Generic equipment manager, Data Access Layer independant.

    It manages the list of rooms' possible equipment.
    Equipment is just a string.

    The list of possible equipment is defined by CRBS admin.

    This list is used mainly for generating user web interface.
    (System must know, what equipment user may ask for to generate [v] checkboxes)
    """

    @staticmethod
    def getPossibleEquipment():
        """ Returns the List of rooms' possible equipment. """
        pass

    @staticmethod
    def setPossibleEquipment( equipmentList ):
        """ Sets the List of rooms' possible equipment. """
        pass

    @staticmethod
    def insertEquipment( equipmentName ):
        """ Adds new equipment to the list of possible equipment. """
        pass

    @staticmethod
    def removeEquipment( equipmentName ):
        """ Deletes the equipment from the list of possible equipment. """
        pass

    @staticmethod
    def removalIsPossible( equipmentName ):
        """ Checks whether any room has the str equipment.
        If so, returns false.
        Else returns true. """
        pass

if __name__ == '__main__':
    pass

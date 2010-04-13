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

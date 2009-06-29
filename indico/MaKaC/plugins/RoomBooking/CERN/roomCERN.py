# -*- coding: utf-8 -*-
##
## $Id: roomCERN.py,v 1.12 2009/05/14 18:05:55 jose Exp $
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

from MaKaC.plugins.RoomBooking.default.room import Room

# Branch name in ZODB root
_ROOMS = 'Rooms'

class RoomCERN( Room ):
    """ 
    ZODB specific implementation. 
    
    For documentation of methods see base class.
    """

    vcList = ["Built-in (MCU) Bridge", "EVO", "Phone Conference", "ESnet collaboration", "HERMES collaboration", "H323 point2point", "ISDN point2point", "I don't know"]


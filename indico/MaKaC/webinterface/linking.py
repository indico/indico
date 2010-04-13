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

"""This file contain several classes which contain the logic needed to allow 
    generating HTML links for some pieces of information about the conferences.
"""
#import MaKaC.conference as conference
from MaKaC.roomMapping import RoomMapperHolder


class RoomLinker:
    """This class is a "facade" for all the room linking system. It constains
        the necessary logic to know which linker object he must appply in order
        to obtain the correct linking for the requests
    """

    def getHTMLLink( self, room, location=None ):
        if room == None:
            return ""
        roomLink = room.getName()
        url = self.getURL( room, location )
        if url != "":
            roomLink = """<a href="%s">%s</a>"""%(url, roomLink)
        return roomLink

    def getURL( self, room, location=None ):
        if location is not None and room is not None:
            res = RoomMapperHolder().match({"name":location.getName()},exact=True)
            if res != []:
                return res[0].getMapURL(room.getName())
        return ""


#class RoomLinker:
#    """This class is a "facade" for all the room linking system. It constains
#        the necessary logic to know which linker object he must appply in order
#        to obtain the correct linking for the requests
#    """
#    
#    def __init__( self ):
#        pass
#
#    def getHTMLLink( self, room, location=None ):
#        if room == None:
#            return ""
#        roomLink = room.getName()
#        url = self.getURL( room, location )
#        if url != "":
#            roomLink = """<a href="%s">%s</a>"""%(url, roomLink)
#        return roomLink
#
#    def getURL( self, room, location=None ):
#        if location == None or room == None:
#            return "" #In the future, when there will be linked locations/rooms
#                      # it will extract the location from the room
#        if isinstance( location, conference.CustomLocation ):
#            linker = CustomRoomLinker()
#            return linker.getURL( room, location )
#        return ""
#
#
#class CustomRoomLinker:
#    """This class contains the logic allowing to generate links for custom
#        location room objects.
#    """
#
#    def __init__( self ):
#        pass
#
#    def getURL( self, room, location ):
#        if location.getName().upper() == "CERN":
#            linker = CERNCustomRoomLinker()
#            return linker.getURL( room )
#        return ""
#
#
#class CERNCustomRoomLinker:
#    """This class allows to generate links for CERN rooms from CustomRoom 
#        objects.
#    """
#    #For the future, the conferences should hold CERNRoom objects and there 
#    #   should be a CERNRoomLinker which could be more accurate 
#    _mapBaseURL = "http://map.web.cern.ch/map/building?bno="
#
#    def __init__( self ):
#        pass
#
#    def _getMapURL( self, building ):
#        if building == "" or building =="0":
#            return ""
#        return "%s%s"%(self._mapBaseURL, building)
#
#    def getURL( self, room ):
#        if room == None or room.getName()=="":
#            return ""
#        #ToDo: A better filter must be used
#        building = room.getName().split("-")[0].strip()
#        if building == "":
#            return ""
#        return self._getMapURL( building )

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

    def getURLByName( self, room, location=None ):
        if location is not None and room is not None:
            res = RoomMapperHolder().match({"name":location},exact=True)
            if res != []:
                return res[0].getMapURL(room)
        return ""

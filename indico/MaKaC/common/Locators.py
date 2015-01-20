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

from UserDict import UserDict
from types import ListType
from indico.util.json import dumps

class Locator(UserDict):
    """Helper class specialising UserDict (dictionary) which contains a locator
        for an object. This is needed due to the id schema chosen and to the
        web needs: it is a relative id schema (a suboject is given an id which
        is unique only inside its superobject) and we need to uniquely identify
        some objects on the web pages so it is needed to handle the "locator"
        which can be made up of various ids. This class will contain the locator
        and provide methods for using it on the web pages so it's use is
        transparent for client.
    """
    def getJSONForm( self ):
        """Returns the current locator data as a JSON string.
        """
        return dumps(self.data)

    def getURLForm( self ):
        """Returns the current locator ready for being included in a URL.
        """
        l = []
        for item in self.data.keys():
            val = self.data[item]
            if isinstance( val, ListType ):
                for v in val:
                    l.append("%s=%s"%(item, v))
            else:
                l.append("%s=%s"%(item, val))
        return "&".join( l )

    def getWebForm( self ):
        """Returns the current locator for being used in web pages forms
            (hidden parameters)
        """
        l = []
        for item in self.data.keys():
            val = self.data[item]
            if isinstance( val, ListType ):
                for v in val:
                    l.append("""<input type="hidden" name="%s" value="%s">"""%(item, v))
            else:
                l.append("""<input type="hidden" name="%s" value="%s">"""%(item, val))
        return "\n".join( l )





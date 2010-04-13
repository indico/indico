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

from UserDict import UserDict
from types import ListType


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
        
            



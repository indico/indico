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

"""This file contains classes that allow to generate sequencial identifiers.
"""
from persistent import Persistent


class Counter(Persistent):
    """This class implements a simple counter that allows to obtain sequencial
       identifiers consisting of succesive integers
    """

    def __init__(self, initialValue = 0 ):
        self.__count = initialValue

    def _getCount(self):
        """ Returns the next identifier as an integer, without changing the innter state
        """
        return self.__count

    def clone(self):
        """ Clones this counter
        """
        newCounter = Counter(self.__count)
        return newCounter

    def newCount(self, wait=0):
        """Returns a new identifier.
        """
        current = self.__count
        self.__count += 1
        return str(current)
    
    def previewNextCount(self):
        """ Returns the next identifier as a string, without changing the inner state
        """
        return str(self.__count)

    def sync(self,count):
        if count is None or count=="":
            return
        try:
            count=int(count)
        except ValueError:
            return
        if count<self.__count:
            return
        else:
            self.__count=count+1


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

from datetime import datetime
from MaKaC.common import DBMgr


class Statistics:
    """
    """
    pass
    

class CategoryStatistics(Statistics):

    def __init__( self , target ):
        # The category for which we want the statistics is attached to the
        # instance at initialization time (target).
        self._target = target

    def getStatistics( self ):
        # The returned statistics are composed of a dictionary containing other
        # dictionaries (one per statistic).
        if self._target.getNumConferences() != 0:
            #self._target.updateStatistics()
            categStats = self._target.getStatistics()
            return categStats
        return None
    
    def updateStatistics(cls, cat):
        cat.updateStatistics()
    updateStatistics = classmethod(updateStatistics) 

    

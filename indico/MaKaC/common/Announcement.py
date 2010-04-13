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

from persistent import Persistent
from MaKaC.common import db



class AnnoucementMgr(Persistent):
    
    def __init__(self):
        self.speed = "2"
        self.text = ""
    
    # TODO: Speed should be removed since no longer used.
    def setSpeed(self, speed):
        self.speed = speed
    
    def getSpeed(self):
        return self.speed
    
    def setText(self, text):
        self.text = text
    
    def getText(self):
        return self.text



def getAnnoucementMgrInstance():
    dbmgr = db.DBMgr.getInstance()
    root = dbmgr.getDBConnection().root()        
    try:
        am = root["AnnoucementMgr"]
    except KeyError, e:
        am = AnnoucementMgr()
        root["AnnoucementMgr"] = am
    return am
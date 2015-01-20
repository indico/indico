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

from persistent import Persistent
from indico.core.db import DBMgr


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
    dbmgr = DBMgr.getInstance()
    root = dbmgr.getDBConnection().root()
    try:
        am = root["AnnoucementMgr"]
    except KeyError, e:
        am = AnnoucementMgr()
        root["AnnoucementMgr"] = am
    return am

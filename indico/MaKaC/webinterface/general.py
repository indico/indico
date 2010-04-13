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

#some general functions
def strfFileSize( sizeInBytes ):
    sizeInBytes = int(sizeInBytes)
    if sizeInBytes < 1024:
        return "%s bytes"%sizeInBytes
    sizeInKBs = sizeInBytes/1024
    if sizeInKBs < 1024:
        return "%s KB"%sizeInKBs
    sizeInMBs = sizeInKBs/1024
    if sizeInMBs < 1024:
        return "%s MB"%sizeInMBs
    sizeInGBs = sizeInMBs/1024
    if sizeInGBs < 1024:
        return "%s GB"%sizeInGBs

def normaliseListParam( param ):
    if not isinstance(param, list):
            return [ param ]
    return param       

class WebFactory:
    ##Don't remove this commentary. Its purpose is to be sure that those words/sentences are in the dictionary after extraction. It also prevents the developper to create an init for this class and update the 283 Webfactory occurences...
    ##_("not defined")
    ##_("no description")

    name = "not defined"
    description = "no description"
    id = ""

    def getId( cls ):
        return cls.id
    getId = classmethod( getId )

    def getName( cls ):
        return _(cls.name)
    getName = classmethod( getName )

    def getDescription( cls ):
        return _(cls.description)
    getDescription = classmethod( getDescription )

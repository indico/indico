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

"""File containing MaKaC exception class hierarchy
"""
from MaKaC.i18n import _

class MaKaCError(Exception):

    def __init__( self, msg="",area="" ):
        self._msg = msg
        self._area = area

    def getMsg( self ):
        return self._msg
    
    def __str__(self):
        if self._area != "":
            return "%s - %s"%(self._area,self._msg)  
        else:
            return self._msg

    def getArea(self):
        return self._area


class AccessControlError(MaKaCError):
    """
    """
    def __init__(self, objectType="object"):
        self.objType = objectType

    def __str__( self ):
        return _("you are not authorised to access this %s")%self.objType
    
class ConferenceClosedError(MaKaCError):
    """
    """
    def __init__(self, conf):
        self._conf = conf

    def __str__( self ):
        return _("the event has been closed")
    


class DomainNotAllowedError(AccessControlError):
    
    def __str__( self ):
        return _("your domain is not allowed to acces this %s")%self.objType


class AccessError(AccessControlError):
    """
    """
    pass

class HostnameResolveError(MaKaCError):
    """
    Hostname resolution failed
    """

class ModificationError(AccessControlError):
    """
    """
    def __str__( self ):
        return _("you are not authorised to modify this %s")%self.objType

class AdminError(AccessControlError):
    """
    """
    def __str__(self):
        return _("only administrators can access this %s")%self.objType

class WebcastAdminError(AccessControlError):
    """
    """
    def __str__(self):
        return "only webcast administrators can access this %s"%self.objType
    
class TimingError(MaKaCError):
    """
    """
    def __init__( self, msg="",area=""):
        self._msg = msg
        self._area = area

class ParentTimingError(TimingError):
    """
    """
    pass

class EntryTimingError(TimingError):
    """
    """
    pass

class UserError(MaKaCError):
    """
    """
    def init(self, msg = ""):
        self._msg = msg
    
    def __str__(self):
        if self._msg:
            return self._msg
        else:
            return _("Error creating user")

class FormValuesError(MaKaCError):
    """
    """
    def __init__( self, msg="",area=""):
        self._msg = msg
        self._area = area

class NoReportError(MaKaCError):
    """
    """
    def __init__( self, msg="", area=""):
        self._msg = msg
        self._area = area
        
class PluginError(MaKaCError):
    pass
    

class htmlScriptError(MaKaCError):
    """
    """
    pass

class htmlForbiddenTag(MaKaCError):
    """
    """
    pass

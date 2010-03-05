# -*- coding: utf-8 -*-
##
## $Id: accessControl.py,v 1.14 2008/08/11 12:00:27 pferreir Exp $
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

import ZODB
from persistent import Persistent

from MaKaC.common import DBMgr
from MaKaC.common import info
import MaKaC

class AccessController( Persistent ):
    """This class keeps access control information both for accessing and 
        modifying which can be related to any conference object. The fact that
        we have a separated class which handles this allows us to reuse the code
        and have a common policy.
       Objects of this class provide 2 list of users (one contains the users
        who can access the related object and another one the users which can
        modify it) along wiht methods for managing them (granting or revoking
        privileges).
       Conference objects can delegate the access control to one of this 
        objects so they don't need to implement again the AC mechanism.
       Parameters:
        __accessProtection -- (int) Flag which indicates whether the resource
            the current access controller is related to is protected (on) or 
            not (off).
        managers -- (PList) List of recognised users or groups (Principal)
            allowed to modify the related resource
        allowed -- (PList) List of recognised users or groups (Principal)
            allowed to access the related resource
    """

    def __init__( self ):
        self._accessProtection = 0
        self._fatherProtection = 0
        self._hideFromUnauthorizedUsers = 0
        self.managers = []
        self.managersEmail = []
        self.allowed = []
        self.allowedEmail = []
        self.requiredDomains = []
        self.accessKey = ""
        self.owner = None
    
    def getOwner(self):
        return self.owner
    
    def setOwner(self, owner):
        self.owner = owner

    def _getAccessProtection( self ):
        try:
            return self._accessProtection
        except:
            self._accessProtection = 0
            return 0

    def getAccessProtectionLevel( self ):
        return self._getAccessProtection()
    
    def _getFatherProtection( self ):
        try:
            return self._fatherProtection
        except:
            self._fatherProtection = 0
            return 0
            
    def isHidden( self ):
        try:
            return self._hideFromUnauthorizedUsers
        except:
            self._hideFromUnauthorizedUsers = 0
            return 0

    def setHidden(self, hidden):
        self._hideFromUnauthorizedUsers = hidden
        self._p_changed = 1

    def isProtected( self ):
        """tells whether the associated resource is read protected or not"""
        return (self._getAccessProtection() + self._getFatherProtection()) > 0

    def isItselfProtected(self):
        return self._getAccessProtection() > 0

    def setProtection( self, protected ):
        self._accessProtection = protected
        self._p_changed = 1

    def isFatherProtected(self):
        return self._getFatherProtection()

    def setFatherProtection( self, protected ):
        self._fatherProtection = protected
        self._p_changed = 1

    def grantAccess( self, principal ):
        """grants read access for the related resource to the specified 
            principal"""
        if principal not in self.allowed and (isinstance(principal, MaKaC.user.Avatar) or isinstance(principal, MaKaC.user.CERNGroup) or isinstance(principal, MaKaC.user.Group)):
            self.allowed.append( principal )
            self._p_changed = 1
    
    def getAccessEmail(self):
        try:
            return self.allowedEmail
        except:
            self.allowedEmail = []
        return self.allowedEmail
    
    def grantAccessEmail(self, email):
        if not email in self.getAccessEmail():
            self.getAccessEmail().append(email)
    
    def revokeAccessEmail(self, email):
        if email in self.getAccessEmail.keys():
            self.getAccessEmail().remove(email)
        

    def revokeAccess( self, principal ):
        """revokes read access for the related resource to the specified 
            principal"""
        #ToDo: Revoking access to a user is quite more complex than this. We can
        #   just remove the user, but if there's a group in the list that 
        #   contains the user, the access to the user is not revoked, he still 
        #   has access. But dunno what to do in that case: raise an exception??
        #   Certainly removing the user from the group or the group itself
        #   wouldn't be acceptable solutions.
        if principal in self.allowed:
            self.allowed.remove( principal )
            self._p_changed = 1

    def setAccessKey( self, key="" ):
        self.accessKey = key
                
    def getAccessKey( self ):
        try:
            return self.accessKey
        except:
            self.setAccessKey()
            return ""
            
    def canKeyAccess( self, key ):
        """
        """
        if self.getAccessKey()!="":
            if key == self.getAccessKey():
                return True
        return False

    @classmethod
    def isHarvesterIP( cls, ip ):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        ipList = minfo.getOAIPrivateHarvesterList()[:]

        if ip in ipList:
            # let Private OAI harvesters access protected (display) pages
            return True
        else:
            return False


    def canIPAccess( self, ip ):
        """
        """

        #Domain protection
        if len(self.getRequiredDomainList())<=0:
            return True
        for domain in self.getRequiredDomainList():
            if domain.belongsTo( ip ):
                return True
        return False

    def isAdmin( self, av ):
        if AdminList.getInstance().isAdmin( av ):
            return True
        else:
            return False

    def canUserAccess( self, av ):
        if self.isAdmin( av ):
            return True
        for principal in self.allowed:
            if principal == None:
                self.revokeAccess(principal)
                continue
            if (isinstance(principal, MaKaC.user.Avatar) or isinstance(principal, MaKaC.user.CERNGroup) or isinstance(principal, MaKaC.user.Group)) and principal.containsUser( av ):
                return True
        if isinstance(av, MaKaC.user.Avatar):
            for email in av.getEmails():
                if email in self.getAccessEmail():
                    self.grantAccess(av)
                    self.revokeAccessEmail(email)
                    av.linkTo(self.getOwner(), "manager")
        #self._v_canuseraccess[av] = False
        #return self._v_canuseraccess[av]
        return False
    
    def getAccessList( self ):
        """returns a list of those principals which have access privileges"""
        return self.allowed
    
    def getModificationEmail(self):
        try:
            return self.managersEmail
        except:
            self.managersEmail = []
        return self.managersEmail
    
    def grantModificationEmail(self, email):
        """looks if the email is in the managersEmail list (list with the users with access to modification)
        and if it's not it adds the email to the list"""
        if not email in self.getModificationEmail():
            self.getModificationEmail().append(email)
            self._p_changed = 1
    
    def revokeModificationEmail(self, email):
        if email in self.getModificationEmail():
            self.getModificationEmail().remove(email)
            self._p_changed = 1
    
    def grantModification( self, principal ):
        """grants modification access for the related resource to the specified 
            principal"""
        # ToDo: should the groups allowed to be managers?
        if principal not in self.managers and (isinstance(principal, MaKaC.user.Avatar) or isinstance(principal, MaKaC.user.CERNGroup) or isinstance(principal, MaKaC.user.Group)):
            self.managers.append( principal )
            self._p_changed = 1

    def revokeModification( self, principal ):
        """revokes modification access for the related resource to the 
            specified principal"""
        if principal in self.managers:
            self.managers.remove( principal )
            self._p_changed = 1

    def canModify( self, user ):
        """tells whether the specified user has modification privileges"""
        #try:
        #    return self._v_canmodify[user]
        #except AttributeError:
        #    self._v_canmodify = {}
        #except KeyError:
        #    pass
        if AdminList.getInstance().isAdmin( user ):
            #self._v_canmodify[user] = 1
            #return self._v_canmodify[user]
            return True
        for principal in self.managers:
            if (isinstance(principal, MaKaC.user.Avatar) or isinstance(principal, MaKaC.user.CERNGroup) or isinstance(principal, MaKaC.user.Group)) and principal.containsUser( user ):
                #self._v_canmodify[user] = 1
                #return self._v_canmodify[user]
                return True
        ret = False
        if isinstance(user, MaKaC.user.Avatar):
            for email in user.getEmails():
                if email in self.getModificationEmail():
                    self.grantModification(user)
                    self.revokeModificationEmail(email)
                    ret = True
                    user.linkTo(self.getOwner(), "manager")
        return ret
        
        #self._v_canmodify[user] = 0
        #return self._v_canmodify[user]
        #return False
    
    def getModifierList( self ):
        """returns a list of those principals which have modification 
            privileges"""
        if None in self.managers:
            self.revokeModification(None)
        return self.managers

    def requireDomain( self, domain ):
        """adds a domain to the required domain list
        """
        if domain in self.requiredDomains:
            return
        self.requiredDomains.append( domain )
        self._p_changed = 1

    def freeDomain( self, domain ):
        """
        """
        if domain not in self.requiredDomains:
            return
        self.requiredDomains.remove( domain )
        self._p_changed = 1

    def getRequiredDomainList( self ):
        """
        """
        return self.requiredDomains
    
    def isDomainProtected(self):
        if self.getRequiredDomainList():
            return 1
        return 0


class CategoryAC(AccessController):
    
    def __init__( self ):
        pass



class _AdminList(Persistent):
    
    def __init__(self):
        self.__list = []

    def grant( self, user ):
        if user not in self.__list:
            self.__list.append( user )
            self._p_changed=1

    def revoke( self, user ):
        if user in self.__list:
            self.__list.remove( user )
            self._p_changed=1

    def isAdmin( self, user ):
        if user in self.__list:
            return True
        from MaKaC.user import Group
        for p in self.__list:
            if type(p) is Group and p.containsUser(user):
                return True
        return False

    def getList( self ):
        return self.__list


class AdminList:
    
    def getInstance( self ):
        dbroot = DBMgr.getInstance().getDBConnection().root()
        if dbroot.has_key("adminlist"):
            return dbroot["adminlist"]
        al = _AdminList()
        dbroot["adminlist"] = al
        return al
    getInstance = classmethod(getInstance)


class AccessWrapper:
    """This class encapsulates the information about an access to the system. It
            must be initialised by clients if they want to perform access 
            control operations over the objects in the system.
    """
    
    def __init__( self ):
        self._currentUser = None
        self._ip = ""
        self._session = None

    def setUser( self, newAvatar ):
        self._currentUser = newAvatar

    def getUser( self ):
        return self._currentUser

    def setIP( self, newIP ):
        self._ip = newIP

    def getIP( self ):
        return self._ip

    def setSession( self, newSession ):
        self._session = newSession

    def getSession( self ):
        return self._session


if __name__ == "__main__":
    pass
    

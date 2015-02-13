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

import ZODB
import itertools
from persistent import Persistent
from functools import wraps

from indico.core.db import DBMgr
from MaKaC.common import info
import MaKaC
from MaKaC.common.contextManager import ContextManager
from MaKaC.plugins import Observable
from MaKaC.common.logger import Logger

def isFullyAccess(level):
    def wrap(func):
        @wraps(func)
        def decorator(*args):
            # if protected and checking for fully public OR
            # if not protected and checking for full private
            if (args[0].isProtected() and level == - 1) or (not args[0].isProtected() and level == 1):
                return False
            for child in args[0].getNonInheritingChildren():
                if child.getAccessController().getAccessProtectionLevel() != level:
                    return False
            return True
        return decorator
    return wrap

def getChildren(level):
    def wrap(func):
        @wraps(func)
        def decorator(*args):
            return [child for child in args[0].getNonInheritingChildren()
                    if child.getAccessController().getAccessProtectionLevel() != level]
        return decorator
    return wrap

class AccessController( Persistent, Observable ):
    """This class keeps access control information both for accessing and
        modifying which can be related to any conference object. The fact that
        we have a separated class which handles this allows us to reuse the code
        and have a common policy.
       Objects of this class provide 2 list of users (one contains the users
        who can access the related object and another one the users which can
        modify it) along with methods for managing them (granting or revoking
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
        submitters -- (PList) List of recognised chairpersons/speakers allowed to manage event materials
    """

    def __init__( self, owner ):
        self._accessProtection = 0
        self._fatherProtection = 0
        self._hideFromUnauthorizedUsers = 0
        self.managers = []
        self.managersEmail = []
        self.allowed = []
        self.allowedEmail = []
        self.requiredDomains = []
        self.accessKey = ""
        self.owner = owner
        self.contactInfo = ""
        self.submitters = []
        self.nonInheritingChildren = set()

    def getOwner(self):
        return self.owner

    def setOwner(self, owner):
        self.owner = owner

    def unlinkAvatars(self, role):
        for prin in itertools.chain(self.getSubmitterList(), self.managers, self.allowed):
            if isinstance(prin, MaKaC.user.Avatar):
                prin.unlinkTo(self.owner, role)

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
            from MaKaC.conference import Conference
            if isinstance(self.getOwner(), Conference):
                ownerList = self.getOwner().getOwnerList()
            else:
                ownerList = [self.getOwner().getOwner()]
            for o in ownerList:
                if o is not None and o.isProtected():
                    return 1
            return 0

            #return self._fatherProtection
        except:
            #Logger.get('accessController').exception('_getFatherProtection')
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

        # TODO: make this extensible
        if principal not in self.allowed and \
               (isinstance(principal, MaKaC.user.Avatar) or \
                isinstance(principal, MaKaC.user.Group)):
            self.allowed.append( principal )
            self._p_changed = 1
        self._notify('accessGranted', principal)

    def getAccessEmail(self):
        try:
            return self.allowedEmail
        except:
            self.allowedEmail = []
        return self.allowedEmail

    def grantAccessEmail(self, email):
        if not email in self.getAccessEmail():
            self.getAccessEmail().append(email)
        self._notify('accessGranted', email)

    def revokeAccessEmail(self, email):
        if email in self.getAccessEmail.keys():
            self.getAccessEmail().remove(email)
        self._notify('accessRevoked', email)

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
        self._notify('accessRevoked', principal)

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
        ipList = minfo.getIPBasedACLMgr().get_full_access_acl()

        return ip in ipList

    def canIPAccess(self, ip):

        # Domain protection
        if not self.getRequiredDomainList():
            return True
        return any(domain.belongsTo(ip) for domain in self.getRequiredDomainList())

    def isAdmin(self, av):
        return AdminList.getInstance().isAdmin(av)

    def canUserAccess(self, av):
        if self.isAdmin(av):
            return True
        for principal in self.allowed:
            if principal is None:
                self.revokeAccess(principal)
                continue
            if (isinstance(principal, MaKaC.user.Avatar) or isinstance(principal, MaKaC.user.Group)) and \
               principal.containsUser(av):
                return True
        if isinstance(av, MaKaC.user.Avatar):
            for email in av.getEmails():
                if email in self.getAccessEmail():
                    self.grantAccess(av)
                    self.revokeAccessEmail(email)
                    av.linkTo(self.getOwner(), "manager")
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
        and if it's not it adds the email to the list
            Returns True is email was added to the list, False if it was already there.
        """
        if not email.lower() in map(lambda x: x.lower(), self.getModificationEmail()):
            self.getModificationEmail().append(email)
            self._p_changed = 1
            self._notify('modificationGranted', email)
            return True
        return False

    def revokeModificationEmail(self, email):
        if email in self.getModificationEmail():
            self.getModificationEmail().remove(email)
            self._p_changed = 1
        self._notify('modificationRevoked', email)

    def grantModification( self, principal ):
        """grants modification access for the related resource to the specified
            principal"""
        # ToDo: should the groups allowed to be managers?
        if principal not in self.managers and (isinstance(principal, MaKaC.user.Avatar) or isinstance(principal, MaKaC.user.Group)):
            self.managers.append( principal )
            self._p_changed = 1
        self._notify('modificationGranted', principal)

    def revokeModification( self, principal ):
        """revokes modification access for the related resource to the
            specified principal"""
        if principal in self.managers:
            self.managers.remove( principal )
            self._p_changed = 1
        self._notify('modificationRevoked', principal)

    def canModify( self, user ):
        """tells whether the specified user has modification privileges"""
        if AdminList.getInstance().isAdmin( user ):
            return True

        for principal in self.managers:
            if (isinstance(principal, MaKaC.user.Avatar) or isinstance(principal, MaKaC.user.Group)) and principal.containsUser( user ):
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

    def getAnyDomainProtection(self):
        """
        Checks if the element is protected by domain at any level. It stops checking
        when it finds some domain protection or a restricted owner.

        Returns the list of domains from which the item can be accessed.
        """
        if self.getAccessProtectionLevel() != 0:
            return []
        elif self.isDomainProtected():
            return self.getRequiredDomainList()
        elif self.getOwner().getOwner():
            return self.getOwner().getOwner().getAccessController().getAnyDomainProtection()
        return []

    def isDomainProtected(self):
        if self.getRequiredDomainList():
            return 1
        return 0

    def getAnyContactInfo(self):
        parent = self.getOwner().getOwner()
        if not self.getContactInfo() and parent and  hasattr(parent, 'getAccessController'):
            return parent.getAccessController().getAnyContactInfo()
        else:
            return self.getContactInfo()

    def getContactInfo(self):
        """Defines who to contact in case of access control error.
        One can use this info to display it along with the exception message"""
        try:
            if self.contactInfo:
                pass
        except AttributeError:
            self.contactInfo = ""
        return self.contactInfo

    def setContactInfo(self, info):
        self.contactInfo = info

    def _grantSubmission(self, av):
        if av not in self.getSubmitterList():
            self.submitters.append(av)
            self._p_changed = 1

    def grantSubmission(self, sb):
        """Grants submission privileges for the specified user
        """
        av = self._getAvatarByEmail(sb.getEmail())
        if av and av.isActivated():
            self._grantSubmission(av)
        elif sb.getEmail():
            self.getOwner().getConference().getPendingQueuesMgr().addSubmitter(sb, self.getOwner(), False)

    def _revokeSubmission(self, av):
        if av in self.getSubmitterList():
            self.submitters.remove(av)
            self._p_changed = 1

    def revokeSubmission(self, sb):
        """Removes submission privileges for the specified user
        """
        av = self._getAvatarByEmail(sb.getEmail())
        self.getOwner().getConference().getPendingQueuesMgr().removeSubmitter(sb, self.getOwner())
        self._revokeSubmission(av)

    def _getAvatarByEmail(self, email):
        from MaKaC.user import AvatarHolder
        ah = AvatarHolder()
        avatars = ah.match({"email": email}, exact=1, searchInAuthenticators=False)
        if not avatars:
            avatars = ah.match({"email": email}, exact=1)
        for av in avatars:
            if av.hasEmail(email):
                return av
        return None

    def getSubmitterList(self, no_groups=False):
        """Gives the list of users with submission privileges
        """
        try:
            return self.submitters
        except AttributeError:
            self.submitters = []
            return self.submitters

    def canUserSubmit(self, user):
        """Tells whether a user can submit material
        """
        return user in self.getSubmitterList()

    def addNonInheritingChildren(self, obj):
        self.nonInheritingChildren.add(obj)
        self._p_changed = 1

    def removeNonInheritingChildren(self, obj):
        self.nonInheritingChildren.discard(obj)
        self._p_changed = 1

    def getNonInheritingChildren(self):
        return self.nonInheritingChildren

    def setNonInheritingChildren(self, nonInheritingChildren):
        self.nonInheritingChildren = nonInheritingChildren

    def updateNonInheritingChildren(self, elem, delete=False):
        if delete or elem.getAccessController().getAccessProtectionLevel() == 0:
            self.removeNonInheritingChildren(elem)
        else:
            self.addNonInheritingChildren(elem)
        self._p_changed = 1

    @isFullyAccess(-1)
    def isFullyPublic(self):
        pass

    @isFullyAccess(1)
    def isFullyPrivate(self):
        pass

    @getChildren(-1)
    def getProtectedChildren(self):
        pass

    @getChildren(1)
    def getPublicChildren(self):
        pass


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
        else:
            # TODO: this is just a workaround for users which id
            # is "Nice:jbgl@cern.ch"
            for u in self.__list:
                if u.getEmail() in user.getEmails():
                    self.__list.remove(u)
                    self._p_changed=1
                    break

    def revokeById( self, userId ):
        for u in self.__list:
            if u.getId() == userId:
                self.__list.remove(u)
                self._p_changed=1
                return True
        else:
            return False

    def isAdmin( self, user ):
        if user in self.__list:
            return True
        from MaKaC.user import Group
        for p in self.__list:
            if isinstance(p, Group) and p.containsUser(user):
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

    def __init__( self, user=None ):
        self._currentUser = user
        self._ip = ""

    def setUser( self, newAvatar ):
        self._currentUser = newAvatar
        ContextManager.set('currentUser', self._currentUser)

    def getUser( self ):
        return self._currentUser

    def setIP( self, newIP ):
        self._ip = newIP

    def getIP( self ):
        return self._ip

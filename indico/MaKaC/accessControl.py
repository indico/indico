# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

import itertools

from persistent import Persistent

from indico.core import signals
from indico.modules.users.legacy import AvatarUserWrapper
from indico.modules.groups.legacy import GroupWrapper
from MaKaC.common import info
from MaKaC.common.contextManager import ContextManager


class AccessController(Persistent):
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

    def getOwner(self):
        raise NotImplementedError('getOwner')
        return self.owner

    def setOwner(self, owner):
        self.owner = owner

    def unlinkAvatars(self, role):
        # XXX: this is never called for a Conference AC, so we don't need a check to skip (old) managers
        for prin in itertools.chain(self.managers, self.allowed):
            if isinstance(prin, AvatarUserWrapper):
                prin.unlinkTo(self.owner, role)

    def _getAccessProtection( self ):
        try:
            return self._accessProtection
        except:
            self._accessProtection = 0
            return 0

    def getAccessProtectionLevel( self ):
        raise NotImplementedError('getAccessProtectionLevel')
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
        except Exception:
            self._fatherProtection = 0
            return 0

    def isHidden( self ):
        try:
            return self._hideFromUnauthorizedUsers
        except AttributeError:
            self._hideFromUnauthorizedUsers = 0
            return 0

    def setHidden(self, hidden):
        self._hideFromUnauthorizedUsers = hidden
        self._p_changed = 1

    def isProtected( self ):
        """tells whether the associated resource is read protected or not"""
        raise NotImplementedError('isProtected')
        return (self._getAccessProtection() + self._getFatherProtection()) > 0

    def isItselfProtected(self):
        raise NotImplementedError('itItselfProtected')
        return self._getAccessProtection() > 0

    def setProtection( self, protected ):
        raise NotImplementedError('setProtection')
        self._accessProtection = protected
        self._p_changed = 1

    def isFatherProtected(self):
        raise NotImplementedError('isFatherProtected')
        return self._getFatherProtection()

    def setFatherProtection( self, protected ):
        self._fatherProtection = protected
        self._p_changed = 1

    def grantAccess(self, principal):
        """grants read access for the related resource to the specified
            principal"""
        if principal not in self.allowed and isinstance(principal, (AvatarUserWrapper, GroupWrapper)):
            self.allowed.append(principal)
            self._p_changed = 1
        # signals.acl.access_granted.send(self, principal=principal)

    def getAccessEmail(self):
        raise NotImplementedError('getAccessEmail')
        try:
            return self.allowedEmail
        except:
            self.allowedEmail = []
        return self.allowedEmail

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
        # signals.acl.access_revoked.send(self, principal=principal)

    @classmethod
    def isHarvesterIP( cls, ip ):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        ipList = minfo.getIPBasedACLMgr().get_full_access_acl()

        return ip in ipList

    def canIPAccess(self, ip):
        raise NotImplementedError('canIPAccess')
        # Domain protection
        if not self.getRequiredDomainList():
            return True
        return any(domain.belongsTo(ip) for domain in self.getRequiredDomainList())

    def isAdmin(self, av):
        raise NotImplementedError('isAdmin')
        return av and av.user and av.user.is_admin

    def canUserAccess(self, av):
        raise NotImplementedError('canUserAccess')
        if self.isAdmin(av):
            return True
        for principal in self.allowed:
            if principal is None:
                self.revokeAccess(principal)
                continue
            if isinstance(principal, (AvatarUserWrapper, GroupWrapper)) and principal.containsUser(av):
                return True
        if isinstance(av, AvatarUserWrapper):
            for email in av.getEmails():
                if email in self.getAccessEmail():
                    self.grantAccess(av)
                    av.linkTo(self.getOwner(), "manager")
        return False

    def getAccessList(self):
        """returns a list of those principals which have access privileges"""
        raise NotImplementedError('getAccessList')
        for principal in list(self.allowed):
            if principal is None:
                self.revokeAccess(principal)
            elif isinstance(principal, AvatarUserWrapper) and principal.user is None:
                self.revokeAccess(principal)
        return self.allowed

    def getModificationEmail(self):
        raise NotImplementedError('getModificationEmail')
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
            # signals.acl.modification_granted.send(self, principal=email)
            return True
        return False

    def revokeModificationEmail(self, email):
        if email in self.getModificationEmail():
            self.getModificationEmail().remove(email)
            self._p_changed = 1
        # signals.acl.modification_revoked.send(self, principal=email)

    def grantModification( self, principal ):
        """grants modification access for the related resource to the specified
            principal"""
        # ToDo: should the groups allowed to be managers?
        if principal not in self.managers and (isinstance(principal, (AvatarUserWrapper, GroupWrapper))):
            self.managers.append(principal)
            self._p_changed = 1
        # signals.acl.modification_granted.send(self, principal=principal)

    def revokeModification( self, principal ):
        """revokes modification access for the related resource to the
            specified principal"""
        if principal in self.managers:
            self.managers.remove( principal )
            self._p_changed = 1
        # signals.acl.modification_revoked.send(self, principal=principal)

    def canModify(self, user):
        """tells whether the specified user has modification privileges"""
        raise NotImplementedError('canModify')
        if user and user.user.is_admin:
            return True

        for principal in self.managers:
            if isinstance(principal, (AvatarUserWrapper, GroupWrapper)) and principal.containsUser(user):
                return True
        ret = False
        if isinstance(user, AvatarUserWrapper):
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
        raise NotImplementedError('getModifierList')
        for principal in list(self.managers):
            if principal is None:
                self.revokeModification(principal)
            elif isinstance(principal, AvatarUserWrapper) and principal.user is None:
                self.revokeModification(principal)
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
        raise NotImplementedError('getRequiredDomainList')
        return self.requiredDomains

    def getAnyDomainProtection(self):
        """
        Checks if the element is protected by domain at any level. It stops checking
        when it finds an explicitly public or private parent.

        Returns the list of domains from which the item can be accessed.
        """
        raise NotImplementedError('getAnyDomainProtection')
        if self.getAccessProtectionLevel() == 0:
            owner = self.getOwner().getOwner()

            # inheriting  - get protection from parent
            if owner:
                return owner.getAccessController().getAnyDomainProtection()
            else:
                # strangely enough, the root category has 2 states
                # 0 -> inheriting (public) and 1 -> restricted
                # so, in this case, we really want the category's list
                return self.getRequiredDomainList()
        else:
            return self.getRequiredDomainList()

    def isDomainProtected(self):
        raise NotImplementedError('isDomainProtected')
        if self.getRequiredDomainList():
            return 1
        return 0

    def getAnyContactInfo(self):
        raise NotImplementedError('getAnyContactInfo')
        parent = self.getOwner().getOwner()
        if not self.getContactInfo() and parent and  hasattr(parent, 'getAccessController'):
            return parent.getAccessController().getAnyContactInfo()
        else:
            return self.getContactInfo()

    def getContactInfo(self):
        """Defines who to contact in case of access control error.
        One can use this info to display it along with the exception message"""
        raise NotImplementedError('getContactInfo')
        try:
            if self.contactInfo:
                pass
        except AttributeError:
            self.contactInfo = ""
        return self.contactInfo

    def setContactInfo(self, info):
        self.contactInfo = info


class AccessWrapper:
    """This class encapsulates the information about an access to the system. It
            must be initialised by clients if they want to perform access
            control operations over the objects in the system.
    """

    def __init__(self, user=None):
        self._currentUser = user

    def setUser( self, newAvatar ):
        self._currentUser = newAvatar
        ContextManager.set('currentUser', self._currentUser)

    def getUser( self ):
        return self._currentUser

    @property
    def user(self):
        return self._currentUser.as_new if self._currentUser else None

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

"""
Asynchronous request handlers for category-related services.
"""

import datetime
from itertools import islice
from MaKaC.services.implementation.base import ProtectedModificationService, ParameterManager
from MaKaC.services.implementation.base import ProtectedDisplayService, ServiceBase
from MaKaC.services.implementation.base import TextModificationBase
import MaKaC.conference as conference
from MaKaC.common.logger import Logger
from MaKaC.services.interface.rpc.common import ServiceError, ServiceAccessError
import MaKaC.webinterface.locators as locators
from MaKaC.webinterface.wcomponents import WConferenceList, WConferenceListEvents
from MaKaC.common.fossilize import fossilize
from MaKaC.user import PrincipalHolder, Avatar, Group
from indico.core.index import Catalog


class CategoryBase(object):
    """
    Base class for category
    """

    def _checkParams( self ):
        try:
            l = locators.WebLocator()
            l.setCategory( self._params )
            self._target = self._categ = l.getObject()
        except:
            #raise ServiceError("ERR-E4", "Invalid category id.")
            self._target = self._categ = conference.CategoryManager().getRoot()


class CategoryModifBase(ProtectedModificationService, CategoryBase):
    def _checkParams(self):
        CategoryBase._checkParams(self)
        ProtectedModificationService._checkParams(self)

class CategoryDisplayBase(ProtectedDisplayService, CategoryBase):

    def _checkParams(self):
        CategoryBase._checkParams(self)
        ProtectedDisplayService._checkParams(self)

class CategoryTextModificationBase(TextModificationBase, CategoryModifBase):
    #Note: don't change the order of the inheritance here!
    pass

class GetCategoryList(CategoryDisplayBase):

    def _checkProtection( self ):
        self._accessAllowed = False
        try:
            CategoryDisplayBase._checkProtection(self)
            self._accessAllowed = True
        except Exception, e:
            pass

    def _getAnswer( self ):
        # allowed is used to report to the user in case of forbidden access.
        allowed = self._accessAllowed

        # if the category access is forbidden we return the previous
        # one which the user can access.
        if  not self._accessAllowed:
            while (not self._accessAllowed and not self._target.isRoot()):
                self._target = self._target.getOwner()
                self._checkProtection()
        target = self._target

        # if the category is final we return the previous one.
        if not target.hasSubcategories():
            target = target.getOwner()

        # We get the parent category. If no parent (Home) we keep the same as target.
        parent = target.getOwner()
        if not parent:
            parent = target

        # Breadcrumbs
        breadcrumbs = target.getCategoryPathTitles()

        # Getting the list of subcategories
        categList=[]
        for cat in target.getSubCategoryList():
            #if cat.hasAnyProtection():
            #    protected = True
            #elif cat.isConferenceCreationRestricted():
            #    protected = not cat.canCreateConference( self._getUser() )
            #else:
            #    protected = False
            categList.append({"id":cat.getId(), "title":cat.getTitle(), "subcatLength":len(cat.getSubCategoryList()), "final": not cat.hasSubcategories()})
        return {"parentCateg":
                    {"id":parent.getId(), "title":parent.getTitle()},
                "currentCateg":
                    {"id":target.getId(), "title":target.getTitle(), "breadcrumb": breadcrumbs},
                "categList":categList,
                "accessAllowed": allowed
                }

class CanCreateEvent(CategoryDisplayBase):
    """
    This service returns whether or not the user can create
    an event in this category along with the protection of
    the chosen category.
    """
    def _checkProtection( self ):
        self._accessAllowed = False
        try:
            CategoryDisplayBase._checkProtection(self)
            self._accessAllowed = True
        except Exception, e:
            pass

    def _getAnswer( self ):
        canCreate = False
        protection = "public"

        if (self._accessAllowed and self._categ.canCreateConference( self._getUser() )):
            canCreate = True

        if self._categ.isProtected() :
            protection = "private"

        return {"canCreate": canCreate,
                "protection": protection}


class GetPastEventsList(CategoryDisplayBase):

    def _checkParams(self):
        CategoryDisplayBase._checkParams(self)
        self._lastIdx = int(self._params.get("lastIdx"))

    def _getAnswer( self ):
        index = Catalog.getIdx('categ_conf_sd').getCategory(self._categ.getId())
        pastEvents = list(islice(index.itervalues(), self._lastIdx))
        return WConferenceListEvents(pastEvents, self._aw).getHTML()

class SetShowPastEventsForCateg(CategoryDisplayBase):

    def _checkParams(self):
        CategoryDisplayBase._checkParams(self)
        self._showPastEvents = bool(self._params.get("showPastEvents",False))

    def _getAnswer( self ):
        session = self._aw.getSession()
        if not session.getVar("fetchPastEventsFrom"):
            session.setVar("fetchPastEventsFrom",set())

        fpef = session.getVar("fetchPastEventsFrom")
        cid = self._categ.getId()

        if self._showPastEvents:
            # check to avoid unnecessary session write (and db write)
            if cid not in fpef:
                fpef.add(cid)
                session.setVar("fetchPastEventsFrom", fpef)
        else:
            fpef.remove(cid)
            session.setVar("fetchPastEventsFrom", fpef)

class CategoryProtectionUserList(CategoryModifBase):
    def _getAnswer(self):
        #will use IAvatarFossil or IGroupFossil
        return fossilize(self._categ.getAllowedToAccessList())

class CategoryProtectionAddUsers(CategoryModifBase):
    def _checkParams(self):

        CategoryModifBase._checkParams(self)

        self._usersData = self._params['value']
        self._user = self.getAW().getUser()

    def _getAnswer(self):

        for user in self._usersData :

            userToAdd = PrincipalHolder().getById(user['id'])

            if not userToAdd :
                raise ServiceError("ERR-U0","User does not exist!")

            self._categ.grantAccess(userToAdd)

class CategoryProtectionRemoveUser(CategoryModifBase):

    def _checkParams(self):
        CategoryModifBase._checkParams(self)

        self._userData = self._params['value']

        self._user = self.getAW().getUser()

    def _getAnswer(self):

        userToRemove = PrincipalHolder().getById(self._userData['id'])

        if not userToRemove :
            raise ServiceError("ERR-U0","User does not exist!")
        elif isinstance(userToRemove, Avatar) or isinstance(userToRemove, Group) :
            self._categ.revokeAccess(userToRemove)

class CategoryContactInfoModification( CategoryTextModificationBase ):
    """
    Category contact email modification
    """
    def _handleSet(self):
        self._categ.getAccessController().setContactInfo(self._value)
    def _handleGet(self):
        return self._categ.getAccessController().getContactInfo()

methodMap = {
    "getCategoryList": GetCategoryList,
    "getPastEventsList": GetPastEventsList,
    "setShowPastEventsForCateg": SetShowPastEventsForCateg,
    "canCreateEvent": CanCreateEvent,
    "protection.getAllowedUsersList": CategoryProtectionUserList,
    "protection.addAllowedUsers": CategoryProtectionAddUsers,
    "protection.removeAllowedUser": CategoryProtectionRemoveUser,
    "protection.changeContactInfo": CategoryContactInfoModification
    }

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
"""
Asynchronous request handlers for category-related services.
"""

from datetime import datetime
from flask import session
from indico.util.redis import suggestions
from itertools import islice
from MaKaC.services.implementation.base import ProtectedModificationService, ParameterManager
from MaKaC.services.implementation.base import ProtectedDisplayService
from MaKaC.services.implementation.base import TextModificationBase
from MaKaC.services.implementation.base import ExportToICalBase
from MaKaC.services.implementation.base import LoggedOnlyService

import MaKaC.conference as conference
from MaKaC.services.interface.rpc.common import ServiceError, ServiceAccessError
import MaKaC.webinterface.locators as locators
from MaKaC.webinterface.wcomponents import WConferenceListItem
from MaKaC.common.fossilize import fossilize
from MaKaC.user import PrincipalHolder, Avatar, Group, AvatarHolder
from indico.core.index import Catalog
from indico.web.http_api.util import generate_public_auth_request
from indico.util.redis import write_client as redis_write_client
import MaKaC.common.info as info
from MaKaC import domain
from indico.core.config import Config
from MaKaC.webinterface.mail import GenericMailer, GenericNotification
from MaKaC.webinterface.urlHandlers import UHCategModifAC

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
        skip = max(0, self._lastIdx - 100)
        pastEvents = {}
        num = 0
        for event in islice(index.itervalues(), skip, self._lastIdx):
            sd = event.getStartDate()
            key = (sd.year, sd.month)
            if key not in pastEvents:
                pastEvents[key] = {
                    'events': [],
                    'title': datetime(sd.year, sd.month, 1).strftime("%B %Y"),
                    'year': sd.year,
                    'month': sd.month
                }
            eventHTML = WConferenceListItem(event, self._aw).getHTML()
            pastEvents[key]['events'].append(eventHTML)
            num += 1
        for monthData in pastEvents.itervalues():
            monthData['events'].reverse()
        return {
            'num': num,
            'events': [v for k, v in sorted(pastEvents.iteritems(), reverse=True)]
        }

class SetShowPastEventsForCateg(CategoryDisplayBase):

    def _checkParams(self):
        CategoryDisplayBase._checkParams(self)
        self._showPastEvents = bool(self._params.get("showPastEvents",False))

    def _getAnswer(self):
        fpef = session.setdefault('fetchPastEventsFrom', set())
        cid = self._categ.getId()

        if self._showPastEvents:
            fpef.add(cid)
        else:
            fpef.remove(cid)
        session.modified = True

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

class CategoryControlUserListBase(CategoryModifBase):

    def _checkParams(self):
        CategoryModifBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._kindOfList = pm.extract("kindOfList", pType=str, allowEmpty=False)

    def _getControlUserList(self):
        if self._kindOfList == "modification":
            result = fossilize(self._categ.getManagerList())
            # get pending users
            for email in self._categ.getAccessController().getModificationEmail():
                pendingUser = {}
                pendingUser["email"] = email
                pendingUser["pending"] = True
                result.append(pendingUser)
            return result
        elif self._kindOfList == "confCreation":
            return fossilize(self._categ.getConferenceCreatorList())


class CategoryAddExistingControlUser(CategoryControlUserListBase):

    def _checkParams(self):
        CategoryControlUserListBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._userList = pm.extract("userList", pType=list, allowEmpty=False)
        self._sendEmailManagers = pm.extract("sendEmailManagers", pType=bool, allowEmpty=True, defaultValue = True)

    def _sendMail(self, currentList, newManager):
        if isinstance(newManager, Avatar):
            managerName = newManager.getStraightFullName()
        else:
            managerName = newManager.getName()
        text = _("""Dear managers,

%s has been added as manager for the category '%s':

%s

Best regards,
Indico Team
        """) % (managerName, self._categ.getName(), UHCategModifAC.getURL(self._categ))
        maildata = { "fromAddr": "%s" % Config.getInstance().getNoReplyEmail(), "toList": [manager.getEmail() for manager in currentList], "subject": "New category manager", "body": text }
        GenericMailer.send(GenericNotification(maildata))


    def _getAnswer(self):
        ph = PrincipalHolder()
        if self._kindOfList == "modification":
            currentList = self._categ.getManagerList()[:]
            for user in self._userList:
                newManager = ph.getById(user["id"])
                self._categ.grantModification(newManager)
                if self._sendEmailManagers and len(currentList) > 0:
                    self._sendMail(currentList, newManager)
        elif self._kindOfList == "confCreation":
            for user in self._userList:
                self._categ.grantConferenceCreation(ph.getById(user["id"]))
        return self._getControlUserList()


class CategoryRemoveControlUser(CategoryControlUserListBase):

    def _checkParams(self):
        CategoryControlUserListBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._userId = pm.extract("userId", pType=str, allowEmpty=False)

    def _getAnswer(self):
        ph = PrincipalHolder()
        if self._kindOfList == "modification":
            self._categ.revokeModification(ph.getById(self._userId))
        elif self._kindOfList == "confCreation":
            self._categ.revokeConferenceCreation(ph.getById(self._userId))
        return self._getControlUserList()

class CategoryExportURLs(CategoryDisplayBase, ExportToICalBase):

    def _checkParams(self):
        CategoryDisplayBase._checkParams(self)
        ExportToICalBase._checkParams(self)

    def _getAnswer(self):
        result = {}

        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()

        urls = generate_public_auth_request(self._apiMode, self._apiKey, '/export/categ/%s.ics'%self._target.getId(), {}, minfo.isAPIPersistentAllowed() and self._apiKey.isPersistentAllowed(), minfo.isAPIHTTPSRequired())
        result["publicRequestURL"] = urls["publicRequestURL"]
        result["authRequestURL"] =  urls["authRequestURL"]
        return result

class CategoryProtectionToggleDomains(CategoryModifBase):

    def _checkParams(self):
        self._params['categId'] = self._params['targetId']
        CategoryModifBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._domainId = pm.extract("domainId", pType=str)
        self._add = pm.extract("add", pType=bool)

    def _getAnswer(self):
        dh = domain.DomainHolder()
        d = dh.getById(self._domainId)
        if self._add:
            self._target.requireDomain(d)
        elif not self._add:
            self._target.freeDomain(d)


class CategoryBasketBase(LoggedOnlyService, CategoryDisplayBase):

    def _checkParams(self):
        LoggedOnlyService._checkParams(self)
        CategoryDisplayBase._checkParams(self)
        userId = ParameterManager(self._params).extract('userId', pType=str, allowEmpty=True)
        if userId is not None:
            self._avatar = AvatarHolder().getById(userId)
        else:
            self._avatar = self._aw.getUser()

    def _checkProtection(self):
        LoggedOnlyService._checkProtection(self)
        CategoryDisplayBase._checkProtection(self)
        if not self._avatar.canUserModify(self._aw.getUser()):
            raise ServiceAccessError('Access denied')


class CategoryFavoriteAdd(CategoryBasketBase):

    def _getAnswer(self):
        if self._categ is conference.CategoryManager().getRoot():
            raise ServiceError('ERR-U0', _('Cannot add root category as favorite'))
        self._avatar.linkTo(self._categ, 'favorite')
        if redis_write_client:
            suggestions.unignore(self._avatar, 'category', self._categ.getId())
            suggestions.unsuggest(self._avatar, 'category', self._categ.getId())

    def _checkParams(self):
        CategoryDisplayBase._checkParams(self)
        CategoryBasketBase._checkParams(self)

    def _checkProtection(self):
        LoggedOnlyService._checkProtection(self)
        CategoryBasketBase._checkProtection(self)
        CategoryDisplayBase._checkProtection(self)


class CategoryFavoriteDel(CategoryBasketBase):

    def _getAnswer(self):
        self._avatar.unlinkTo(self._categ, 'favorite')
        if redis_write_client:
            suggestions.unsuggest(self._avatar, 'category', self._categ.getId())

    def _checkParams(self):
        CategoryDisplayBase._checkParams(self)
        CategoryBasketBase._checkParams(self)

    def _checkProtection(self):
        LoggedOnlyService._checkProtection(self)
        CategoryBasketBase._checkProtection(self)
        CategoryDisplayBase._checkProtection(self)


class CategorySuggestionDel(CategoryBasketBase):
    def _getAnswer(self):
        suggestions.unsuggest(self._avatar, 'category', self._categ.getId(), True)

    def _checkParams(self):
        CategoryDisplayBase._checkParams(self)
        CategoryBasketBase._checkParams(self)

    def _checkProtection(self):
        LoggedOnlyService._checkProtection(self)
        CategoryBasketBase._checkProtection(self)
        CategoryDisplayBase._checkProtection(self)


methodMap = {
    "getCategoryList": GetCategoryList,
    "getPastEventsList": GetPastEventsList,
    "setShowPastEventsForCateg": SetShowPastEventsForCateg,
    "canCreateEvent": CanCreateEvent,
    "protection.getAllowedUsersList": CategoryProtectionUserList,
    "protection.addAllowedUsers": CategoryProtectionAddUsers,
    "protection.removeAllowedUser": CategoryProtectionRemoveUser,
    "protection.changeContactInfo": CategoryContactInfoModification,
    "protection.removeManager": CategoryRemoveControlUser,
    "protection.addExistingConfCreator": CategoryAddExistingControlUser,
    "protection.removeConfCreator": CategoryRemoveControlUser,
    "protection.toggleDomains": CategoryProtectionToggleDomains,
    "api.getExportURLs": CategoryExportURLs,
    "favorites.addCategory": CategoryFavoriteAdd,
    "favorites.delCategory": CategoryFavoriteDel,
    "suggestions.delSuggestion": CategorySuggestionDel
}

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
Schedule-related services
"""

from MaKaC.services.interface.rpc.common import ServiceError, ServiceAccessError,NoReportError
from MaKaC.services.implementation.base import \
     ParameterManager, ProtectedModificationService, ProtectedDisplayService

import MaKaC.webinterface.locators as locators
from MaKaC.errors import ModificationError

import MaKaC.conference as conference
from MaKaC.user import AvatarHolder, GroupHolder
from MaKaC.common.fossilize import fossilize
from MaKaC.fossils.conference import IMaterialFossil,\
        ILinkFossil, ILocalFileFossil, ILocalFileExtendedFossil
from MaKaC.common.PickleJar import DictPickler
from MaKaC.webinterface.rh.contribMod import RCContributionPaperReviewingStaff


class UserListChange(object):

    def changeUserList(self, object, newList):
        # clone the list, to avoid problems
        allowedUsers = object.getAllowedToAccessList()[:]

        # user can be a user or group
        for user in allowedUsers:
            if not user.getId() in newList:
                object.revokeAccess(user)
            else:
                del newList[user.getId()]

        for elem in newList:
            # TODO: Change this, when DictPickler goes away
            if ('isGroup' in elem and elem['isGroup']) or \
                   ('_fossil' in elem and elem['_fossil'] == 'group'):
                avatar = GroupHolder().getById(elem['id'])
            else:
                avatar = AvatarHolder().getById(elem['id'])
            object.grantAccess(avatar)


class MaterialBase:

    def _checkParams( self ):
        try:
            l = locators.WebLocator()

            self._material = None
            self._conf = None

            l.setMaterial( self._params, 0 )
            self._target = l.getObject()


            #if isinstance(self._target, conference.Material):
            self._material = self._target
            self._conf = self._target.getConference()
            if self._conf == None:
                self._categ = self._target
            else:
                self._categ = self._conf.getOwner()

            ## TODO: remove this, since material/resource creation
            ## doesn't come through this method

            ## if isinstance(self._target, conference.Category):
            ##     self._categ = self._target
            ## else:
            ##     self._conf = self._target.getConference()

            ## if self._conf == None:
            ##     self._categ=self._target.getCategory()


        except Exception, e:
            if self._target is None:
                raise NoReportError(_("The material with does not exist anymore. Please refresh the page."))
            else:
                raise ServiceError("ERR-M0", str(e))

class MaterialDisplayBase(ProtectedDisplayService, MaterialBase):

    def _checkParams(self):
        MaterialBase._checkParams(self)
        ProtectedDisplayService._checkParams(self)

class MaterialModifBase(MaterialBase, ProtectedModificationService):

    def _checkParams(self):
        MaterialBase._checkParams(self)
        ProtectedModificationService._checkParams(self)

    def _checkProtection(self):
        owner = self._material.getOwner()

        # Conference submitters have access
        if isinstance(owner, conference.Conference) and owner.getAccessController().canUserSubmit(self._aw.getUser()):
            return

        # There are two exceptions to the normal permission scheme:
        # (sub-)contribution submitters and session coordinators

        # in case the owner is a (sub-)contribution, we should
        # allow submitters
        if isinstance(owner, conference.Contribution) or \
           isinstance(owner, conference.SubContribution):

            reviewingState = self._material.getReviewingState()

            if (reviewingState < 3 and # it means the papers has not been submitted yet (or not reviewing material)
                owner.canUserSubmit(self._aw.getUser())):
                # Submitters have access
                return
            # status = 3 means the paper is under review (submitted but not reviewed)
            # status = 2 means that the author has not yet submitted the material
            elif isinstance(owner, conference.Contribution) and RCContributionPaperReviewingStaff.hasRights(self, contribution = owner, includingContentReviewer=False) and reviewingState in [2, 3]:
                return
            elif owner.getSession() and \
                     owner.getSession().canCoordinate(self._aw, "modifContribs"):
                # Coordinators of the parent session have access
                return

        # if it's associated with a session, coordinators
        # should be allowed
        elif self._material.getSession() != None and \
            self._material.getSession().canCoordinate(self._aw):
            # Session coordinators have access
            return

        try:
            ProtectedModificationService._checkProtection(self)
        except ModificationError:
            raise ServiceAccessError(_("you are not authorised to manage material "
                                       "for this contribution"))
class ResourceBase:
    """
    Base class for material resource access
    """

    def _checkParams(self):
        """
        Checks the materialId, and retrieves the material using it
        """

        self._material = None
        self._conf = None

        l = locators.WebLocator()

        try:

            l.setResource( self._params, 0 )
            self._target = l.getObject()

            if isinstance(self._target, conference.Resource):
                self._resource = self._target
                self._material = self._target.getOwner()

            if isinstance(self._target, conference.Material):
                self._material = self._target

            if isinstance(self._target, conference.Category):
                self._categ = self._target
            else:
                self._conf = self._target.getConference()

            if self._conf == None:
                self._categ=self._target.getCategory()

        except Exception, e:
            if self._target is None:
                raise NoReportError(_("The resource with does not exist anymore. Please refresh the page."))

            else:
                raise ServiceError("ERR-M0", str(e))


class ResourceDisplayBase(ProtectedDisplayService, ResourceBase):

    def _checkProtection(self):
        ProtectedDisplayService._checkParams(self)

    def _checkParams(self):
        ResourceBase._checkParams(self)
        ProtectedDisplayService._checkParams(self)

class ResourceModifBase(ResourceBase, MaterialModifBase):

    def _checkParams(self):
        ResourceBase._checkParams(self)


class GetMaterialClassesBase(MaterialDisplayBase):
    """
    Base class for obtaining a listing of material classes
    """

    def _checkParams( self ):
        l = locators.WebLocator()

        l.setMaterial( self._params, 0 )
        self._target = l.getObject()


    def _getAnswer(self):
        """
        Provides the list of material classes, based on the target
        resource (conference, session, contribution, etc...)
        """
        matList = {}

        for mat in self._target.getAllMaterialList():
            matList[mat.getId()] = mat.fossilize(IMaterialFossil)

        return matList

class GetReviewingMaterial(GetMaterialClassesBase):
    """
    Base class for obtaining a listing of reviewing material classes
    """

    def _checkProtection(self):
        if not RCContributionPaperReviewingStaff.hasRights(self):
            GetMaterialClassesBase._checkProtection(self)

    def _getAnswer(self):
        """
        Provides the list of material classes, based on the target
        resource (conference, session, contribution, etc...)
        """

        matList = {}
        rev = self._target.getReviewing()
        if (rev != None and len(rev._Material__resources) != 0):
            reviewManager = self._target.getReviewManager()
            matList[rev.getId()] = rev.fossilize(IMaterialFossil)
            matList[rev.getId()]["isUnderReview"] = rev.getReviewingState() == 2 and len(reviewManager.getVersioning()) > 1
        return matList


class GetMaterial(MaterialDisplayBase):
    """
    Service for obtaining a material by id
    """

    def _getAnswer(self):
        """
        Provides the list of material classes, based on the target
        resource (conference, session, contribution, etc...)
        """
        return self._material.fossilize(IMaterialFossil)

class GetMaterialAllowedUsers(MaterialModifBase):
    """
    Lists the users that allowed to access the material
    """

    def _checkParams(self):
        MaterialModifBase._checkParams(self)
        self._includeFavList = self._params.get("includeFavList", False)
        self._user = self._getUser() #will be None if user is not authenticated

    def _getAnswer(self):
        #will use IAvatarFossil or IGroupFossil
        allowedAccesList = fossilize(self._material.getAllowedToAccessList())
        if self._includeFavList and self._user:
            favList = fossilize(
                self._user.getPersonalInfo().getBasket().getUsers().values())

            return [allowedAccesList, favList]
        else:
            return allowedAccesList


class GetMaterialProtection(MaterialModifBase):

    def _getAnswer(self):
        """
        Returns the material's protection
        """
        try:
            materialId = self._target.getMaterialById(self._params['matId'])
        except:
            # it's not in the material list, we return the parent's level of protection
            # WATCH OUT! This is the default value to inherit from parent in Editor.js.
            # if that value is changed for any reason this function may not
            # work properly
            return 0
        else:
            return materialId.getAccessProtectionLevel()


class SetMainResource(MaterialModifBase):

    def _getAnswer(self):
        self._target.setMainResource(self._target.getResourceById(self._params['resourceId']))


class RemoveMainResource(MaterialModifBase):

    def _getAnswer(self):
        self._target.setMainResource(None)


class EditMaterialClassBase(MaterialModifBase, UserListChange):
    """
    Base class for material class edition
    """

    def _checkParams(self):
        """
        Gets a reference to the material, using the
        id as the key, and gets the properties to change
        """
        MaterialModifBase._checkParams(self)

        matId = self._params.get("materialId",None)
        self._newProperties = self._params.get("materialInfo",None)
        self._newUserList = self._newProperties['userList']

        materialPM = ParameterManager(self._newProperties)

        self._title = materialPM.extract('title', pType=str, allowEmpty=True, defaultValue="NO TITLE ASSIGNED")
        self._description = materialPM.extract('description', pType=str, allowEmpty=True)
        self._protection = materialPM.extract('protection', pType=int)
        self._hidden = materialPM.extract('hidden', pType=int)
        self._accessKey = materialPM.extract('accessKey', pType=str, allowEmpty=True)

    def _getAnswer(self):
        """
        Updates the material with the new properties
        """

        if self._material.isBuiltin() and self._material.getTitle() != self._title:
            raise ServiceError("", "You can't change the name of a built-in material.")

        self.changeUserList(self._material, self._newUserList)

        self._material.setTitle(self._title);
        self._material.setDescription(self._description);
        self._material.setProtection(self._protection);
        self._material.setHidden(self._hidden);
        self._material.setAccessKey(self._accessKey);

        event = self._material.getOwner()
        materialRegistry = event.getMaterialRegistry()

        return {
            'material': self._material.fossilize(IMaterialFossil),
            'newMaterialTypes': materialRegistry.getMaterialList(event)
            }

class DeleteMaterialClassBase(MaterialModifBase):

    def _getAnswer(self):
        materialId = self._material.getId()
        event = self._material.getOwner()

        # actually delete it
        self._target.getOwner().removeMaterial(self._material)

        materialRegistry = event.getMaterialRegistry()

        return {
            'deletedMaterialId': materialId,
            'newMaterialTypes': materialRegistry.getMaterialList(event)
            }

class GetResourcesBase(ResourceDisplayBase):

    def _getAnswer(self):
        resList = {}

        for resource in self._material.getResourceList():
            resList[resource.getId()] = resource.fossilize({"MaKaC.conference.Link": ILinkFossil,
                                                           "MaKaC.conference.LocalFile": ILocalFileFossil})
        return resList

class EditResourceBase(ResourceModifBase, UserListChange):

    def _checkParams(self):
        ResourceModifBase._checkParams(self)

        self._newProperties = self._params.get("resourceInfo",None)
        self._newUserList = self._newProperties['userList']

    def _getAnswer(self):

        self.changeUserList(self._resource, self._newUserList)

        DictPickler.update(self._resource, self._newProperties)
        return self._resource.fossilize({"MaKaC.conference.Link": ILinkFossil,
                                        "MaKaC.conference.LocalFile": ILocalFileExtendedFossil})

class GetResourceAllowedUsers(ResourceModifBase):
    """
    Lists the users that allowed to access the resource
    """

    def _checkParams(self):
        ResourceModifBase._checkParams(self)
        self._includeFavList = self._params.get("includeFavList", False)
        self._user = self._getUser() #will be None if user is not authenticated

    def _getAnswer(self):
        #will use IAvatarFossil or IGroupFossil
        allowedAccesList = fossilize(self._resource.getAllowedToAccessList())
        if self._includeFavList and self._user:
            favList = fossilize(self._user.getPersonalInfo().getBasket().getUsers().values())
            return [allowedAccesList, favList]
        else:
            return allowedAccesList


class DeleteResourceBase(ResourceModifBase):

    def _deleteResource(self):
        # remove the resource
        self._material.removeResource(self._resource)
        self._event = self._material.getOwner()

        # if there are no resources left inside the material,
        # just delete it
        if len(self._material.getResourceList()) == 0:
            self._event.removeMaterial(self._material)


class DeleteResource(DeleteResourceBase):

    def _getAnswer(self):
        self._deleteResource()
        return {
            'deletedResourceId': self._resource.getId(),
            'newMaterialTypes': self._event.getMaterialRegistry().getMaterialList(self._event)
            }

class DeleteResourceReviewing(DeleteResourceBase):

    def _getAnswer(self):
        self._deleteResource()
        return {
            'deletedResourceId': self._resource.getId(),
            'newMaterialTypes': [["reviewing", "Reviewing"]]
            }

methodMap = {

    "list": GetMaterialClassesBase,
    "reviewing.list": GetReviewingMaterial,
    "listAllowedUsers": GetMaterialAllowedUsers,
    "get": GetMaterial,
    "edit": EditMaterialClassBase,
    "delete": DeleteMaterialClassBase,
    "getProtection": GetMaterialProtection,
    "setMainResource": SetMainResource,
    "removeMainResource": RemoveMainResource,

    # Resource add is quite hacky, and uses a normal RH, because of file upload
    # So, you won't find it here...

    "resources.listAllowedUsers": GetResourceAllowedUsers,
    "resources.list": GetResourcesBase,
    "resources.edit": EditResourceBase,
    "resources.delete": DeleteResource,
    "reviewing.resources.delete": DeleteResourceReviewing
    }


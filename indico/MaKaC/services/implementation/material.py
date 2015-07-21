# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

"""
Schedule-related services
"""

from indico.util.user import principal_from_fossil
from MaKaC.services.interface.rpc.common import ServiceError, ServiceAccessError,NoReportError
from MaKaC.services.implementation.base import ProtectedModificationService, ProtectedDisplayService

import MaKaC.webinterface.locators as locators
from MaKaC.errors import ModificationError

import MaKaC.conference as conference
from MaKaC.common.fossilize import fossilize
from MaKaC.fossils.conference import IMaterialFossil, ILinkFossil, ILocalFileExtendedFossil
from MaKaC.common.PickleJar import DictPickler
from MaKaC.webinterface.rh.contribMod import RCContributionPaperReviewingStaff
from indico.util.i18n import _


class UserListChange(object):

    def changeUserList(self, obj, newList):
        # clone the list, to avoid problems
        allowedUsers = obj.getAllowedToAccessList()[:]
        for principal in allowedUsers:
            obj.revokeAccess(principal)
        for principal in map(principal_from_fossil, newList):
            obj.grantAccess(principal)


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


class GetReviewingMaterial(MaterialDisplayBase):
    """
    Base class for obtaining a listing of reviewing material classes
    """

    def _checkParams(self):
        l = locators.WebLocator()
        l.setMaterial(self._params, 0)
        self._target = l.getObject()

    def _checkProtection(self):
        if not RCContributionPaperReviewingStaff.hasRights(self):
            MaterialDisplayBase._checkProtection(self)

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
        self._user = self._getUser() #will be None if user is not authenticated

    def _getAnswer(self):
        #will use IAvatarFossil or IGroupFossil
        return fossilize(self._resource.getAllowedToAccessList())


class DeleteResourceBase(ResourceModifBase):

    def _deleteResource(self):
        # remove the resource
        self._material.removeResource(self._resource)
        self._event = self._material.getOwner()

        # if there are no resources left inside the material,
        # just delete it
        if len(self._material.getResourceList()) == 0:
            self._event.removeMaterial(self._material)


class DeleteResourceReviewing(DeleteResourceBase):

    def _getAnswer(self):
        self._deleteResource()
        return {
            'deletedResourceId': self._resource.getId(),
            'newMaterialTypes': [["reviewing", "Reviewing"]]
            }


methodMap = {
    # everything here is still needed for reviewing!
    # TODO: remove this whole file when migrating reviewing
    "get": GetMaterial,
    "reviewing.list": GetReviewingMaterial,
    "reviewing.resources.delete": DeleteResourceReviewing,
    "resources.listAllowedUsers": GetResourceAllowedUsers,
    "resources.edit": EditResourceBase,
}

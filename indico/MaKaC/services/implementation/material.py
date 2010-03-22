"""
Schedule-related services
"""

import MaKaC.conference as conference

from MaKaC.common.PickleJar import DictPickler
import MaKaC.webinterface.locators as locators
from MaKaC.user import AvatarHolder, GroupHolder

from MaKaC.services.interface.rpc.common import ServiceError, ServiceAccessError

from MaKaC.services.implementation.base import ParameterManager
from MaKaC.services.implementation.base import ProtectedModificationService
from MaKaC.services.implementation.base import ProtectedDisplayService
from MaKaC.errors import ModificationError, MaKaCError
from MaKaC.common.fossilize import fossilize


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
            if 'isGroup' in elem and elem['isGroup']:
                avatar = GroupHolder().getById(elem['id'])
            else:
                avatar = AvatarHolder().getById(elem['id'])
            object.grantAccess(avatar)


class MaterialBase(object):

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

        # There are two exceptions to the normal permission scheme:
        # (sub-)contribution submitters and session coordinators

        # in case the owner is a (sub-)contribution, we should
        # allow submitters
        if isinstance(owner, conference.Contribution) or \
           isinstance(owner, conference.SubContribution):

            reviewingState = self._material.getReviewingState()

            if (reviewingState < 3 and
                owner.canUserSubmit(self._aw.getUser())):
                # Submitters have access
                return
            elif owner.getSession() and owner.getSession().canCoordinate(self._aw, "modifContribs"):
                # Coordinators of the parent session have access
                return

        # if it's associated with a session, coordinators
        # should be allowed
        elif self._material.getSession() != None and \
            self._material.getSession().canCoordinate(self._aw, "modifContribs"):
            # Session coordinators have access
            return

        try:
            ProtectedModificationService._checkProtection(self)
        except ModificationError:
            raise ServiceAccessError("ERR-P5", _("you are not authorised to manage material for this contribution"))
        except Exception, e:
            raise e

class ResourceBase(object):
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

    #def _checkProtection(self):
    #    MaterialModifBase._checkProtection(self)

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
            matList[mat.getId()] = DictPickler.pickle(mat)

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
        return DictPickler.pickle(self._material)


class GetMaterialAllowedUsers(MaterialModifBase):
    """
    Lists the users that allowed to access the material
    """

    def _getAnswer(self):
        #will use IAvatarFossil or IGroupFossil
        return fossilize(self._material.getAllowedToAccessList())

class GetMaterialProtection(MaterialModifBase):

    def _getAnswer(self):
        """
        Returns the material's protection
        """
        try:
            materialId = self._target.getMaterialById(self._params['matId'])
        except:
        #it's not in the material list, we return the parent's level of protection
        #WATCH OUT! This is the default value to inherit from parent in Editor.js, if that value is changed
        #for any reason this function may not work properly
            return 0
        else:
            return materialId.getAccessProtectionLevel()


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

        self.changeUserList(self._material, self._newUserList)

        self._material.setTitle(self._title);
        self._material.setDescription(self._description);
        self._material.setProtection(self._protection);
        self._material.setHidden(self._hidden);
        self._material.setAccessKey(self._accessKey);

        event = self._material.getOwner()
        materialRegistry = event.getMaterialRegistry()

        return {
            'material': DictPickler.pickle(self._material),
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
            resList[resource.getId()] = DictPickler.pickle(resource)
        return resList

class EditResourceBase(ResourceModifBase, UserListChange):

    def _checkParams(self):
        ResourceModifBase._checkParams(self)

        resId = self._params.get("resourceId",None)
        self._newProperties = self._params.get("resourceInfo",None)
        self._newUserList = self._newProperties['userList']

    def _getAnswer(self):

        self.changeUserList(self._resource, self._newUserList)

        DictPickler.update(self._resource, self._newProperties)
        return DictPickler.pickle(self._resource)

class GetResourceAllowedUsers(ResourceModifBase):
    """
    Lists the users that allowed to access the resource
    """

    def _getAnswer(self):
        #will use IAvatarFossil or IGroupFossil
        return fossilize(self._resource.getAllowedToAccessList())


class DeleteResourceBase(ResourceModifBase):

    def _getAnswer(self):
        resourceId = self._resource.getId()

        # remove the resource
        self._material.removeResource(self._resource)

        # if there are no resources left inside the material,
        # just delete it
        if len(self._material.getResourceList()) == 0:
            event = self._material.getOwner()
            event.removeMaterial(self._material)
            newMaterialTypes = event.getMaterialRegistry().getMaterialList(event)
        else:
            newMaterialTypes = []

        return {
            'deletedResourceId': resourceId,
            'newMaterialTypes': newMaterialTypes
            }



methodMap = {

    "list": GetMaterialClassesBase,
    "listAllowedUsers": GetMaterialAllowedUsers,
    "get": GetMaterial,
    "edit": EditMaterialClassBase,
    "delete": DeleteMaterialClassBase,
    "getProtection": GetMaterialProtection,

    # Resource add is quite hacky, and uses a normal RH, because of file upload
    # So, you won't find it here...
    "resources.listAllowedUsers": GetResourceAllowedUsers,
    "resources.list": GetResourcesBase,
    "resources.edit": EditResourceBase,
    "resources.delete": DeleteResourceBase
    }


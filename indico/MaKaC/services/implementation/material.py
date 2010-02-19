"""
Schedule-related services
"""

import MaKaC.conference as conference

from MaKaC.common.PickleJar import DictPickler
import MaKaC.webinterface.locators as locators
from MaKaC.user import AvatarHolder, GroupHolder

from MaKaC.services.interface.rpc.common import ServiceError

from MaKaC.services.implementation.base import ParameterManager
from MaKaC.services.implementation.base import ProtectedModificationService
from MaKaC.services.implementation.base import ProtectedDisplayService
from MaKaC.errors import ModificationError, MaKaCError


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

class MaterialDisplayBase(ProtectedDisplayService, MaterialBase):

    def _checkParams(self):
        MaterialBase._checkParams(self)
        ProtectedDisplayService._checkParams(self)

class MaterialModifBase(MaterialBase, ProtectedModificationService):

    def _checkParams(self):
        MaterialBase._checkParams(self)
        ProtectedModificationService._checkParams(self)

    def _checkProtection(self):

        if self._material: #target is a material
            if isinstance(self._material.getOwner(), conference.Contribution) and \
                self._material.getOwner().canUserSubmit(self._aw.getUser()) and \
                self._material.getReviewingState() < 3:
                return
            elif self._material.getSession() != None and \
                   self._material.getSession().canCoordinate(self._aw, "modifContribs"):
                # Session coordiantors have access
                return
        elif isinstance(self._target, conference.Contribution): #target is a contribution
            if self._target.canUserSubmit(self._aw.getUser()):
                return

        try:
            ProtectedModificationService._checkProtection(self)
        except ModificationError:
            raise ServiceError("ERR-M2", _("you are not authorised to manage material for this contribution"))
        except Exception, e:
            raise e

class ResourceBase(object):
    """
    Base class for material resource access
    """

    #def _checkProtection(self):
    #    """
    #    Makes sure that the user is allowed to view the material the
    #    resource is contained in
    #    """
    #
    #    if not self._material.canView(self._aw):
    #        from MaKaC.services.interface.rpc.common import PermissionError
    #        raise PermissionError("You're not allowed to access these contents")

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

    def _getAnswer(self):
        """
        Lists the users that allowed to access the material
        """
        return DictPickler.pickle(self._material.getAllowedToAccessList())

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

class AddMaterialClassBase(MaterialModifBase):
    """
    Base class for addition of material classes
    """

    def _checkParams(self):
        """
        Gets the parameters for the new material class
        (name and description)
        """
        MaterialModifBase._checkParams(self)
        self._matName = self._params.get('materialName', None)
        self._matDescription = self._params.get('description', None)

    def _getAnswer(self):
        """
        Creates the material class, and sets its properties
        """

        mats = self._target.getMaterialList()

        for m in mats:
            if m.getTitle() == self._matName:
                raise ServiceError("ERR-M1", _("A material with this same name already exists"))

        mat = conference.Material()
        mat.setTitle(self._matName)
        mat.setDescription(self._matDescription)
        self._target.addMaterial( mat )
        return DictPickler.pickle(mat)

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

        return DictPickler.pickle(self._material)

class DeleteMaterialClassBase(MaterialModifBase):

    #def _checkParams(self):
        #matId = self._params.get("materialId",None)
        #
        #if matId == None:
        #    raise ServiceError("No material was specified!")
        #
        #self._material = self._target.getMaterialById(matId)


    def _getAnswer(self):
        id = self._material.getId()
        self._target.getOwner().removeMaterial(self._material)
        return id

class GetResourcesBase(ResourceDisplayBase):

#    def _checkParams(self):
#        ResourceBase._checkParams(self)

#    def _checkProtection(self):
#        ResourceBase._checkProtection(self)

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

#        if resId == None:
#            raise ServiceError("No resource was specified!")
#
#        self._resource = self._material.getResourceById(resId)

#    def _checkProtection(self):
#        ResourceBase._checkProtection(self)

    def _getAnswer(self):

        self.changeUserList(self._resource, self._newUserList)

        DictPickler.update(self._resource, self._newProperties)
        return DictPickler.pickle(self._resource)

class GetResourceAllowedUsers(ResourceModifBase):

    def _getAnswer(self):
        """
        Lists the users that allowed to access the material
        """
        return DictPickler.pickle(self._resource.getAllowedToAccessList())


class DeleteResourceBase(ResourceModifBase):

    def _checkParams(self):
        ResourceModifBase._checkParams(self)

        #resId = self._params.get("resourceId",None)
#
#        if resId == None:
#            raise ServiceError("No resource was specified!")
#
#        self._resource = self._material.getResourceById(resId)

    def _getAnswer(self):
        id = self._resource.getId()

        # remove the resource
        self._material.removeResource(self._resource)

        # if there are no resources left inside the material,
        # just delete it
        if len(self._material.getResourceList()) == 0:
            self._material.getOwner().removeMaterial(self._material)

        return id

#def getMixedInClass(base, mixin):
#    """
#    It would be a pain in the %#@ replicating almost the
#    same code for every class that deals with materials/resources,
#    belonging to conferences, contributions, sessions and
#    subcontributions. Being so, this kind of 'hacky' solution
#    is used.
#    """
#
#    class MixedInClass(mixin, base):
#        """
#        The resulting class, with parameter checking
#        done in the correct order
#        """
#        def _checkParams(self):
#            """
#            Parameter checking: (first base class, i.e. "conference",
#            and then mixin class "add material")
#            """
#            base._checkParams(self)
#            mixin._checkParams(self)
#    return MixedInClass


methodMap = {

    "list": GetMaterialClassesBase,
    "listAllowedUsers": GetMaterialAllowedUsers,
    "add": AddMaterialClassBase,
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


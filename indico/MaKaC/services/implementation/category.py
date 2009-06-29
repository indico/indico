"""
Asynchronous request handlers for category-related services.
"""

from MaKaC.services.implementation.base import ProtectedModificationService, ParameterManager
from MaKaC.services.implementation.base import ProtectedDisplayService, ServiceBase
import MaKaC.conference as conference
from MaKaC.common.logger import Logger
from MaKaC.services.interface.rpc.common import ServiceError
import MaKaC.webinterface.locators as locators

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

    def _checkProtection( self ):
        self._accessAllowed = False
        try:
            CategoryDisplayBase._checkProtection(self)
            self._accessAllowed = True
        except Exception, e:
            pass

    def _getAnswer( self ):
        if (self._accessAllowed and self._categ.canCreateConference( self._getUser() )):
                return True
        return False


methodMap = {
    "getCategoryList": GetCategoryList,
    "canCreateEvent": CanCreateEvent
    }

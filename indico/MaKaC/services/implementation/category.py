"""
Asynchronous request handlers for category-related services.
"""

import datetime
from MaKaC.services.implementation.base import ProtectedModificationService, ParameterManager
from MaKaC.services.implementation.base import ProtectedDisplayService, ServiceBase
import MaKaC.conference as conference
from MaKaC.common.logger import Logger
from MaKaC.services.interface.rpc.common import ServiceError
import MaKaC.webinterface.locators as locators
from MaKaC.webinterface.wcomponents import WConferenceList, WConferenceListEvents

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
        pm = ParameterManager(self._params)
        self._fromDate = pm.extract("fromDate", pType=datetime.datetime, allowEmpty=False).date()

    def _getAnswer( self ):

        allEvents,eventsByMonth = WConferenceList.sortEvents(self._target.getConferenceList())

        ## CREATE future events dict and future/past counter
        pastEvents = {}
        for year in allEvents.keys():
            if year < self._fromDate.year:
                pastEvents[year] = allEvents[year]
            elif year == self._fromDate.year:
                for month in allEvents[year].keys():
                    if month < self._fromDate.month:
                        pastEvents.setdefault(year,{})[month] = allEvents[year][month]

        return WConferenceListEvents(pastEvents, self._aw).getHTML()


methodMap = {
    "getCategoryList": GetCategoryList,
    "getPastEventsList": GetPastEventsList,
    "canCreateEvent": CanCreateEvent
    }

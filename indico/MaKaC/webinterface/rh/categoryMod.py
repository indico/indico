# -*- coding: utf-8 -*-
##
## $Id: categoryMod.py,v 1.32 2009/05/25 13:26:24 eragners Exp $
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

import os,types, tempfile

import MaKaC.webinterface.rh.base as base
import MaKaC.webinterface.locators as locators
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.pages.category as category
from MaKaC.common.Configuration import Config
import MaKaC.common.indexes as indexes 
from MaKaC.common.utils import sortCategoryByTitle
import MaKaC.conference as conference
import MaKaC.user as user
import MaKaC.domain as domain
from MaKaC.common.general import *
from MaKaC.webinterface.rh.base import RHModificationBaseProtected
from MaKaC.errors import MaKaCError
from MaKaC.errors import FormValuesError
#import MaKaC.webinterface.pages.conferences as conferences
import MaKaC.conference as conference
import stat
import MaKaC.webinterface.materialFactories as materialFactories
from MaKaC.conference import LocalFile,Material,Link
from MaKaC.export import fileConverter
from MaKaC.webinterface.rh.conferenceBase import RHSubmitMaterialBase
from MaKaC.i18n import _

class RHCategModifBase( RHModificationBaseProtected ):

    def _checkProtection(self):
        if self._target.canModify( self.getAW() ):
            RHModificationBaseProtected._checkProtection(self)
            return
        else:
            self._redirect(urlHandlers.UHCategoryDisplay.getURL(self._target))

    def _checkParams( self, params ):
        l = locators.CategoryWebLocator( params )
        self._target = l.getObject()
        self._getSession().setVar("currentCategoryId", self._target.getId())


class RHCategoryModification( RHCategModifBase ):
    _uh = urlHandlers.UHCategoryModification
    
    def _process( self ):
        p = category.WPCategoryModification( self, self._target )
        return p.display()


class RHCategoryDataModif( RHCategModifBase ):
    _uh = urlHandlers.UHCategoryDataModif
    
    def _process( self ):
        p = category.WPCategoryDataModification( self, self._target )
        return p.display()

class RHCategoryClearCache( RHCategModifBase ):
    _uh = urlHandlers.UHCategoryClearCache

    def _process( self ):
        self._target.clearCache()
        self._redirect( urlHandlers.UHCategoryModification.getURL( self._target ) )
    
class RHCategoryClearConferenceCaches( RHCategModifBase ):
    _uh = urlHandlers.UHCategoryClearConferenceCaches

    def _process( self ):
        self._target.clearConferenceCaches()
        self._redirect( urlHandlers.UHCategoryModification.getURL( self._target ) )
    
class RHCategoryPerformModification( RHCategModifBase ):
    _uh = urlHandlers.UHCategoryPerformModification
    
    def _checkParams(self, params):
        RHCategModifBase._checkParams(self, params)
        if params.get("name", "").strip() =="":
            raise FormValuesError("Please, provide a name for the new subcategory")    

    def _getNewTempFile( self ):
        cfg = Config.getInstance()
        tempPath = cfg.getUploadedFilesTempDir()
        tempFileName = tempfile.mkstemp( suffix="Indico.tmp", dir = tempPath )[1]
        return tempFileName
    
    def _saveFileToTemp( self, fd ):
        fileName = self._getNewTempFile()
        f = open( fileName, "wb" )
        f.write( fd.read() )
        f.close()
        return fileName
    
    def _process( self):
        params = self._getRequestParams()
          
        if not "cancel" in params:
            if (params.get("subcats","")):
                subcat=True
            else:
                subcat=False
            if (params.get("modifyConfTZ","")):
                modifyConfTZ=True
            else:
                modifyConfTZ=False
            tz = params.get("defaultTimezone", "UTC") 
            self._target.setTimezone( tz )
            if modifyConfTZ:
               self._target.changeConfTimezones( tz )
            self._target.setName( params.get("name", "") )
            self._target.setDescription( params.get("description", "") )
            self._target.setDefaultStyle("simple_event",params.get("defaultSimpleEventStyle", ""),subcat )
            self._target.setDefaultStyle("meeting",params.get("defaultMeetingStyle", ""),subcat)
            if self._target.getVisibility() != int(params.get("visibility",999)):
                self._target.setVisibility(params.get("visibility",999))
            if  "delete" in params and self._target.getIcon() is not None:
                self._target.removeIcon()
            if "icon" in params and not type(params["icon"]) is types.StringType:
                if not hasattr(self, "_filePath"):
                    # do not save the file again if it has already been done (db conflicts)
                    self._filePath = self._saveFileToTemp( params["icon"].file )
                    self._tempFilesToDelete.append(self._filePath)
                self._fileName = params["icon"].filename
                f = conference.LocalFile()
                f.setName( "Icon" )
                f.setDescription( "This is the icon for the category" )
                f.setFileName( self._fileName )
                f.setFilePath( self._filePath )
                self._target.setIcon( f )
            if "tasksAllowed" in params :
                if params["tasksAllowed"] == "allowed" :
                    self._target.setTasksAllowed()
                else :
                    self._target.setTasksForbidden()
                    
        self._redirect( urlHandlers.UHCategoryModification.getURL( self._target ) )


class RHCategoryTaskOption( RHCategModifBase ):    
    _uh = urlHandlers.UHCategoryTasksOption
    
    def _process( self ):
        
        if self._target.tasksAllowed() :            
            self._target.setTasksForbidden()            
        else :
            self._target.setTasksAllowed()
            
        self._redirect( urlHandlers.UHCategoryModification.getURL( self._target ) )



class RHCategoryAC( RHCategModifBase ):
    _uh = urlHandlers.UHCategModifAC
    
    def _process( self ):
        p = category.WPCategModifAC( self, self._target )
        return p.display()
        

class RHCategoryTools( RHCategModifBase ):
    _uh = urlHandlers.UHCategModifTools
    
    def _process( self ):
        p = category.WPCategModifTools( self, self._target )
        return p.display()


class RHCategoryTasks( RHCategModifBase ):
    _uh = urlHandlers.UHCategModifTasks
    
    def _process( self ):
        p = category.WPCategModifTasks( self, self._target )
        return p.display()

class RHCategoryFiles( RHCategModifBase ):
    _uh = urlHandlers.UHCategModifFiles
  
    def _process( self ):       
        p = category.WPCategoryModifExistingMaterials( self, self._target )
        return p.display()
  

class RHAddMaterial( RHCategModifBase ):
    _uh = urlHandlers.UHCategoryAddMaterial
   
    def _checkParams( self, params ):
        RHCategModifBase._checkParams(self, params)
        if not hasattr(self, "_rhSubmitMaterial"):
            self._rhSubmitMaterial=RHSubmitMaterialBase(self._target, self)
        self._rhSubmitMaterial._checkParams(params)

    def _process( self ):
        r=self._rhSubmitMaterial._process(self, self._getRequestParams())
        if r is None:
            self._redirect(self._uh.getURL(self._target))
        return r


class RHCategoryTasksAction( RHCategModifBase ):
    _uh = urlHandlers.UHCategModifTasksAction
    
    def _process( self ):
        params = self._getRequestParams()        
        
        if params.get("accessVisibility","") == _("PRIVATE") :
            self._target.setTasksPrivate()
        elif params.get("accessVisibility","") == _("PUBLIC") :
            self._target.setTasksPublic()
        else :
            pass
            
        if params.get("commentVisibility","") == _("PRIVATE") :
            self._target.setTasksCommentPrivate()
        elif params.get("commentVisibility","") == _("PUBLIC") :
            self._target.setTasksCommentPublic()
        else :
            pass
            
        if params.get("taskAccessAction","") == "Add":
            chosen = params.get("accessChosen",None)
            if chosen is not None and chosen != "" :
                person = self._findPerson(chosen)
                if person is not None :
                    self._target.addTasksAccessPerson(person)
        elif params.get("taskAccessAction","") == "New":
            pass
        elif params.get("taskAccessAction","") == "Remove":
            chosen = self._normaliseListParam(params.get("access", []))
            for c in chosen :
                self._target.removeTasksAccessPerson(int(c))
        else :
            pass
            
        if params.get("taskCommentAction","") == "Add":
            chosen = params.get("commentChosen",None)
            if chosen is not None and chosen != "" :                
                person = self._findPerson(chosen)
                if person is not None :
                    self._target.addTasksCommentator(person)
        elif params.get("taskCommentAction","") == "New":
            pass
        elif params.get("taskCommentAction","") == "Remove":
            chosen = self._normaliseListParam(params.get("commentator", []))
            for c in chosen :
                self._target.removeTasksCommentator(int(c))
        else :
            pass
        
        
        if params.get("taskManagerAction","") == "Add":
            chosen = params.get("managerChosen",None)
            if chosen is not None and chosen != "" :                                
                person = self._findPerson(chosen)
                if person is not None :                    
                    self._target.addTasksManager(person)
        elif params.get("taskManagerAction","") == "New":
            pass
        elif params.get("taskManagerAction","") == "Remove":
            chosen = self._normaliseListParam(params.get("manager", []))
            for c in chosen :
                self._target.removeTasksManager(int(c))
        else :
            pass
        
            
        p = category.WPCategModifTasks( self, self._target )
        return p.display()

    def _findPerson(self, idString): 
        if idString is None or idString == "" :
            return None
        if idString[0] == "c" :
            return self.getTasksCommentator(int(idString[1:]))
        elif idString[0] == "a" :
            return self._target.getTasksAccessPerson(int(idString[1:]))
            
        index = idString.find("-")
        eventId = idString[1:index]
        personId = idString[index+1:]
        
        if idString[0] == "h" :
            return self._target.getConferenceById(eventId).getChairById(personId)
        elif idString[0] == "m" :
            return self._target.getConferenceById(eventId).getManagerList()[int(personId)]
        elif idString[0] == "p" :
            return self._target.getConferenceById(eventId).getParticipation().getParticipantById(personId)
        
        return None

class RHCategoryCreation( RHCategModifBase ):
    _uh = urlHandlers.UHCategoryCreation
    
    def _process( self ):
        p = category.WPCategoryCreation( self, self._target )
        return p.display()


class RHCategoryPerformCreation( RHCategModifBase ):
    _uh = urlHandlers.UHCategoryPerformCreation
   
    def _checkParams(self, params):
        RHCategModifBase._checkParams(self, params)
        if params.get("name", "").strip() =="" and not ("cancel" in params):
            raise FormValuesError("Please, provide a name for the new subcategory")

    def _process( self ):
        params = self._getRequestParams()
        if not ("cancel" in params):
            nc = self._target.newSubCategory()  
            nc.setTimezone( params.get("defaultTimezone"))
            nc.setName( params.get("name", "") )
            nc.setDescription( params.get("description", "") )
            nc.setDefaultStyle("simple_event",params.get("defaultSimpleEventStyle", "") )
            nc.setDefaultStyle("meeting",params.get("defaultMeetingStyle", "") )
        self._redirect( urlHandlers.UHCategoryModification.getURL( self._target ) )


#class RHCategoryRemoveSubItems( RHCategModifBase ):
#    _uh = urlHandlers.UHCategoryPerformCreation
#    
#    def _checkParams( self, params ):
#        RHCategModifBase._checkParams( self, params )
#        self._cancel = False
#        if params.get("cancel"):
#            self._cancel = True
#            return
#        categIdList = self._normaliseListParam(params.get("selectedCateg", []))
#        self._categs = []
#        cm = conference.CategoryManager()
#        for categId in categIdList:
#            self._categs.append( cm.getById( categId ) )
#        confIdList = self._normaliseListParam(params.get( "selectedConf", [] ))
#        self._confs = []
#        ch = conference.ConferenceHolder()
#        for confId in confIdList:
#            self._confs.append( ch.getById( confId ) )
#    
#    def _process( self ):
#        if self._cancel:
#            self._redirect(WPCategoryModification.getURL( self._target ))
#            return "done"


class _ActionSubCategDeletion:
    
    def __init__( self, rh, target, selCategs ):
        self._rh = rh
        self._target = target
        self._categs = selCategs
    
    def askConfirmation( self, params ):
        p = category.WPSubCategoryDeletion( self._rh, self._target )
        return p.display( subCategs=self._categs )

    def perform( self ):
        for categ in self._categs:
            categ.delete()

class _ActionSortCategories:

    def __init__( self, rh ):
        self._rh = rh

    def askConfirmation( self, params ):
        return ""

    def perform(self):
        cl = self._rh._target.getSubCategoryList()
        cl.sort(sortCategoryByTitle)
        for categ in cl:
            categ.setOrder(cl.index(categ))

class _ActionSubCategMove:
    
    def __init__( self, rh, newpos, oldpos ):
        self._rh = rh
        self._newpos = int(newpos)
        self._oldpos = int(oldpos)
        
    def askConfirmation( self, params ):
        return ""

    def perform(self):
        cl = self._rh._target.getSubCategoryList()
        order = 0
        movedcateg = cl[self._oldpos]
        del cl[self._oldpos]
        cl.insert(self._newpos,movedcateg)
        for categ in cl:
            categ.setOrder(cl.index(categ))

class _ActionSubCategReallocation:
    
    def __init__( self, rh, target, selCategs ):
        self._rh = rh
        self._target = target
        self._categs = selCategs
    
    def askConfirmation( self, params ):
        p = category.WPCategoryReallocation( self._rh, self._target )
        params["subCategs"] = self._categs
        return p.display( **params )

    def perform( self ):
        #check if the current user has modification privileges on the 
        #   destination category
        if not self._target.canModify( self._rh.getAW() ):
            raise MaKaCError( _("cannot reallocate selected categoried to the selected destination because you are not authorised to modify the destination category"))
        for categ in self._categs:
            categ.move( self._target ) 


class RHCategoryActionSubCategs( RHCategModifBase ):
    _uh = urlHandlers.UHCategoryActionSubCategs
    
    def _checkParams( self, params ):
        RHCategModifBase._checkParams( self, params )
        categIdList = self._normaliseListParam(params.get("selectedCateg", []))
        self._categs = []
        self._confirmation = params.has_key("confirm")
        if "cancel" in params:
            return
        cm = conference.CategoryManager()
        for categId in categIdList:
            self._categs.append( cm.getById( categId ) )
        self._action = _ActionSubCategDeletion( self, self._target, self._categs )
        if params.has_key("reallocate"):
            self._action = _ActionSubCategReallocation( self, self._target, self._categs )
        if params.has_key("oldpos") and params["oldpos"]!='':
            self._confirmation = 1
            self._action = _ActionSubCategMove( self, params['newpos'+params['oldpos']], params['oldpos'] )
        if params.has_key("sort"):
            self._confirmation = 1
            self._action = _ActionSortCategories( self )
    
    def _process( self ):
        if not self._categs:
            if self._confirmation:
                #Move category
                self._action.perform()
        else:
            if self._confirmation:
                #remove, reallocate
                self._action.perform()
            else:
                return self._action.askConfirmation( self._getRequestParams() )
        self._redirect( urlHandlers.UHCategoryModification.getURL( self._target ) )

class _ActionConferenceDeletion:
    
    def __init__( self, rh,target, selConfs,):
        self._rh = rh
        self._target = target
        self._confs = selConfs

    def perform( self,confs ):
        for event in confs:
            event.delete()

    
    def askConfirmation( self, params ):
        p = category.WPConferenceDeletion( self._rh, self._target )
        return p.display( events=self._confs )

class _ActionConferenceReallocation:
    
    def __init__( self, rh, srcCateg, selConfs, target):
        self._rh = rh
        self._categ = srcCateg
        self._confs = selConfs
        self._target=target
    
    def askConfirmation( self, params ):
        p = category.WPConferenceReallocation( self._rh, self._categ )
        params["confs"] = self._confs
        return p.display( **params )

    def perform( self, confs ):
        #ToDo: check if the current user can create conferences on the 
        #   destination category
        if self._confs == []:
            self._confs = confs
        for conf in self._confs:
            self._categ.removeConference( conf )
            self._target._addConference( conf )


class RHCategoryActionConferences( RHCategModifBase ):
    _uh = urlHandlers.UHCategoryActionConferences
    
    def _checkParams( self, params ):
        RHCategModifBase._checkParams( self, params )
        confIdList = self._normaliseListParam(params.get("selectedConf", []))
        self._confs = []
        self._confirmation = params.has_key("confirm")
        if "cancel" in params:
            return
        ch = conference.ConferenceHolder()
        for confId in confIdList:
            self._confs.append( ch.getById( confId ) )
        self._action = _ActionConferenceDeletion( self, self._target, self._confs, )
        if params.has_key("reallocate"):
            self._srcCateg = self._target
            if self._confirmation:
                cm = conference.CategoryManager()
                self._srcCateg = cm.getById( params["srcCategId"] )
            self._action = _ActionConferenceReallocation( self, self._srcCateg, self._confs, self._target )
    
    def _process( self ):
        if self._confirmation:
            self._action.perform(self._confs)
            self._redirect( urlHandlers.UHCategoryModification.getURL( self._target ) )
        if not self._confs:
            self._redirect( urlHandlers.UHCategoryModification.getURL( self._target ) )
        else:
            return self._action.askConfirmation( self._getRequestParams() )


class RHCategorySelectManagers( RHCategModifBase ):
    _uh = urlHandlers.UHCategorySelectManagers
    
    def _process( self ):
        p = category.WPCategorySelectManagers( self, self._target )
        return p.display( **self._getRequestParams() )


class RHCategoryAddManagers( RHCategModifBase ):
    _uh = urlHandlers.UHCategoryAddManagers
    
    def _process( self ):
        params = self._getRequestParams()
        if "selectedPrincipals" in params and not "cancel" in params:
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                av = ph.getById( id )
                self._target.grantModification( av )
        self._redirect( urlHandlers.UHCategModifAC.getURL( self._target ) )


class RHCategoryRemoveManagers( RHCategModifBase ):
    _uh = urlHandlers.UHCategoryRemoveManagers
    
    def _process( self ):
        params = self._getRequestParams()
        if ("selectedPrincipals" in params) and \
            (len(params["selectedPrincipals"])!=0):
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                self._target.revokeModification( ph.getById( id ) )
        self._redirect( urlHandlers.UHCategModifAC.getURL( self._target ) )


class RHCategorySetVisibility( RHCategModifBase ):
    _uh = urlHandlers.UHCategorySetVisibility
    
    def _process( self ):
        params = self._getRequestParams()
        if params["visibility"] == "PRIVATE":
            self._target.setProtection( 1 )
        elif params["visibility"] == "PUBLIC":
            self._target.setProtection( 0 )
        elif params["visibility"] == "ABSOLUTELY PUBLIC":
            self._target.setProtection( -1 )
        self._redirect( urlHandlers.UHCategModifAC.getURL( self._target ) )
    

class RHCategorySelectAllowed( RHCategModifBase ):
    _uh = urlHandlers.UHCategorySelectAllowed
    
    def _process( self ):
        p = category.WPCategorySelectAllowed( self, self._target )
        return p.display( **self._getRequestParams() )


class RHCategoryAddAllowed( RHCategModifBase ):
    _uh = urlHandlers.UHCategoryAddAllowed
    
    def _process( self ):
        params = self._getRequestParams()
        if "selectedPrincipals" in params and not "cancel" in params:
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                self._target.grantAccess( ph.getById( id ) )
        self._redirect( urlHandlers.UHCategModifAC.getURL( self._target ) )


class RHCategoryRemoveAllowed( RHCategModifBase ):
    _uh = urlHandlers.UHCategoryRemoveAllowed
    
    def _process( self ):
        params = self._getRequestParams()
        if ("selectedPrincipals" in params) and \
            (len(params["selectedPrincipals"])!=0):
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                self._target.revokeAccess( ph.getById( id ) )
        self._redirect( urlHandlers.UHCategModifAC.getURL( self._target ) )


class RHCategoryAddDomains( RHCategModifBase ):
    _uh = urlHandlers.UHCategoryAddDomain
    
    def _process( self ):
        params = self._getRequestParams()
        if ("addDomain" in params) and (len(params["addDomain"])!=0):
            dh = domain.DomainHolder()
            for domId in self._normaliseListParam( params["addDomain"] ):
                self._target.requireDomain( dh.getById( domId ) )
        self._redirect( urlHandlers.UHCategModifAC.getURL( self._target ) )


class RHCategoryRemoveDomains( RHCategModifBase ):
    _uh = urlHandlers.UHCategoryRemoveDomain
    
    def _process( self ):
        params = self._getRequestParams()
        if ("selectedDomain" in params) and (len(params["selectedDomain"])!=0):
            dh = domain.DomainHolder()
            for domId in self._normaliseListParam( params["selectedDomain"] ):
                self._target.freeDomain( dh.getById( domId ) )
        self._redirect( urlHandlers.UHCategModifAC.getURL( self._target ) )


class RHCategorySetConfControl( RHCategModifBase ):
    _uh = urlHandlers.UHCategorySetConfCreationControl

    def _process( self ):
        params = self._getRequestParams()
        if "RESTRICT" in self._getRequestParams():
            self._target.restrictConferenceCreation()
        else:
            self._target.allowConferenceCreation()
        self._redirect( urlHandlers.UHCategModifAC.getURL( self._target ) )


class RHCategorySelectConfCreators( RHCategModifBase ):
    _uh = urlHandlers.UHCategorySelectConfCreators
    
    def _process( self ):
        p = category.WPCategorySelectConfCreators( self, self._target )
        return p.display( **self._getRequestParams() )


class RHCategoryAddConfCreators( RHCategModifBase ):
    _uh = urlHandlers.UHCategoryAddConfCreators
    
    def _process( self ):
        params = self._getRequestParams()
        if "selectedPrincipals" in params and not "cancel" in params:
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                entity = ph.getById( id )
                assert(isinstance(entity, user.Avatar) or
                       isinstance(entity, user.Group))
                self._target.grantConferenceCreation( entity )
        self._redirect( urlHandlers.UHCategModifAC.getURL( self._target ) )


class RHCategoryRemoveConfCreators( RHCategModifBase ):
    _uh = urlHandlers.UHCategoryRemoveConfCreators
    
    def _process( self ):
        params = self._getRequestParams()
        if ("selectedPrincipals" in params) and \
            (len(params["selectedPrincipals"])!=0):
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                self._target.revokeConferenceCreation( ph.getById( id ) )
        self._redirect( urlHandlers.UHCategModifAC.getURL( self._target ) )

class RHCategorySetNotifyCreation( RHCategModifBase ):
    _uh = urlHandlers.UHCategorySetNotifyCreation
    
    def _process( self ):
        params = self._getRequestParams()
        self._target.setNotifyCreationList(params.get("notifyCreationList",""))
        self._redirect( urlHandlers.UHCategModifAC.getURL( self._target ) )

class RHCategoryDeletion( RHCategModifBase ):
    _uh = urlHandlers.UHCategoryDeletion
    
    def _checkParams( self, params ):
        RHCategModifBase._checkParams( self, params )
        self._cancel = False
        if "cancel" in params:
            self._cancel = True
        self._confirmation = params.has_key("confirm")
    
    def _perform( self ):
        self._target.delete(1)
    
    def _process( self ):
        if self._cancel:
            self._redirect( urlHandlers.UHCategModifTools.getURL( self._target ) )
        elif self._confirmation:
            owner = self._target.getOwner()
            self._perform()
            self._redirect( urlHandlers.UHCategoryModification.getURL( owner ) )
        else:
            p = category.WPCategoryDeletion( self, self._target )
            return p.display()


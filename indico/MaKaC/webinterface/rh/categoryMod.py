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

from flask import request
import tempfile

import MaKaC.webinterface.locators as locators
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.pages.category as category
from MaKaC.webinterface.user import UserListModificationBase
from indico.core.config import Config
from MaKaC.common.utils import validMail
from MaKaC.webinterface.rh.base import RHModificationBaseProtected
from MaKaC.errors import MaKaCError, FormValuesError, NotFoundError
import MaKaC.conference as conference

from indico.modules.users.legacy import AvatarUserWrapper
from indico.modules.groups.legacy import GroupWrapper
from indico.util.i18n import _


class RHCategModifBase( RHModificationBaseProtected ):

    def _checkProtection(self):
        if self._target.canModify( self.getAW() ):
            RHModificationBaseProtected._checkProtection(self)
            return
        else:
            self._doProcess = False
            self._redirect(urlHandlers.UHCategoryDisplay.getURL(self._target))

    def _checkParams(self, params):
        l = locators.CategoryWebLocator(params)
        self._target = l.getObject()
        if self._target is None:
            raise NotFoundError(_("The category with id '{}' does not exist or has been deleted").format(
                                params["categId"]),
                                title=_("Category not found"))


class RHCategoryModification(RHCategModifBase):
    _uh = urlHandlers.UHCategoryModification

    def _process(self):
        p = category.WPCategoryModification(self, self._target)
        return p.display()


class RHCategoryDataModif( RHCategModifBase ):
    _uh = urlHandlers.UHCategoryDataModif

    def _process( self ):
        p = category.WPCategoryDataModification( self, self._target )
        return p.display()


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

    def _saveFileToTemp(self, fs):
        fileName = self._getNewTempFile()
        fs.save(fileName)
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

            if params.get("name", "") != self._target.getName():
                self._target.setName( params.get("name", "") )

            self._target.setDescription( params.get("description", "") )
            self._target.setDefaultStyle("simple_event",params.get("defaultSimpleEventStyle", ""),subcat )
            self._target.setDefaultStyle("meeting",params.get("defaultMeetingStyle", ""),subcat)
            if self._target.getVisibility() != int(params.get("visibility",999)):
                self._target.setVisibility(params.get("visibility",999))
            if self._getUser().isAdmin():
                self._target.setSuggestionsDisabled('disableSuggestions' in request.form)
            if "delete" in params and self._target.getIcon() is not None:
                self._target.removeIcon()
            if "icon" in params and type(params["icon"]) != str and \
                   params["icon"].filename.strip() != "":
                if not hasattr(self, "_filePath"):
                    # do not save the file again if it has already been done (db conflicts)
                    self._filePath = self._saveFileToTemp(params["icon"])
                    self._tempFilesToDelete.append(self._filePath)
                self._fileName = params["icon"].filename

                f = conference.LocalFile()
                f.setName( "Icon" )
                f.setDescription( "This is the icon for the category" )
                f.setFileName( self._fileName )
                f.setFilePath( self._filePath )
                self._target.setIcon( f )

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

            categAccessProtection = params.get("categProtection", "inherit")

            if categAccessProtection == "private" :
                protection = 1
            elif categAccessProtection == "public" :
                protection = -1
            else:
                protection = 0

            nc = self._target.newSubCategory(protection)

            nc.setTimezone( params.get("defaultTimezone"))
            nc.setName( params.get("name", "") )
            nc.setDescription( params.get("description", "") )
            nc.setDefaultStyle("simple_event",params.get("defaultSimpleEventStyle", "") )
            nc.setDefaultStyle("meeting",params.get("defaultMeetingStyle", "") )

            if protection == 1:
                allowedUsers = self._getAllowedUsers(params)
                if allowedUsers :
                    for person in allowedUsers :
                        if isinstance(person, (AvatarUserWrapper, GroupWrapper)):
                            nc.grantAccess(person)

        self._redirect( urlHandlers.UHCategoryModification.getURL( self._target ) )


    def _getAllowedUsers(self, params):

        auAvatars = []
        from MaKaC.services.interface.rpc import json
        allowedUsersDict = json.decode(params.get("allowedUsers"))
        if allowedUsersDict :
            auAvatars, auNewUsers, auEditedAvatars = UserListModificationBase.retrieveUsers({"allowedUserList":allowedUsersDict}, "allowedUserList")

        return auAvatars


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
            for manager in categ.getManagerList():
                categ.revokeModification(manager)
            categ.delete()

class _ActionSortCategories:

    def __init__( self, rh ):
        self._rh = rh

    def askConfirmation( self, params ):
        return ""

    def perform(self):
        cl = self._rh._target.getSubCategoryList()
        cl.sort(key=lambda c: c.getTitle().lower())
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
                return self._action.askConfirmation(self._getRequestParams())
        self._redirect(urlHandlers.UHCategoryModification.getURL(self._target))


class _ActionConferenceDeletion:

    def __init__(self, rh, target, selConfs):
        self._rh = rh
        self._target = target
        self._confs = selConfs

    def perform(self, confs):
        for event in confs:
            event.delete()

    def askConfirmation(self, params):
        p = category.WPConferenceDeletion(self._rh, self._target)
        return p.display(events=self._confs)


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

    def perform(self, confs):
        # TODO: check if the current user can create conferences on the destination category
        if not self._confs:
            self._confs = confs
        for conf in self._confs:
            if self._categ == conf.getOwner():
                self._categ.moveConference(conf, self._target)


class RHCategoryActionConferences(RHCategModifBase):
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


class RHCategorySetVisibility( RHCategModifBase ):
    _uh = urlHandlers.UHCategorySetVisibility

    def _process( self ):
        params = self._getRequestParams()
        if params.has_key("changeToPrivate"):
            self._target.setProtection( 1 )
        elif params.has_key("changeToInheriting"):
            self._target.setProtection( 0 )
        elif params.has_key("changeToPublic"):
            # The 'Home' category is handled as a special case.
            # We maintain the illusion for the user of it being either
            # private or public, but actually it can be either private
            # or inheriting for legacy reasons.
            if params["type"] == "Home":
                self._target.setProtection( 0 )
            else :
                self._target.setProtection( -1 )
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


class RHCategorySetNotifyCreation( RHCategModifBase ):
    _uh = urlHandlers.UHCategorySetNotifyCreation

    def _checkParams(self, params):
        RHCategModifBase._checkParams(self, params)
        self._emailList = params.get("notifyCreationList","")
        if self._emailList.strip() != "" and not validMail(self._emailList):
            raise FormValuesError(_("The email list contains invalid e-mail addresses or invalid separator"))

    def _process( self ):
        self._target.setNotifyCreationList(self._emailList)
        self._redirect( urlHandlers.UHCategModifAC.getURL( self._target ) )


class RHCategoryDeletion(RHCategModifBase):
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
            self._redirect(urlHandlers.UHCategoryModification.getURL(owner))
        else:
            p = category.WPCategoryDeletion(self, self._target)
            return p.display()

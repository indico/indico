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
from flask import request

import tempfile
import os
import shutil
import MaKaC.webinterface.locators as locators
import MaKaC.webinterface.webFactoryRegistry as webFactoryRegistry
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.common import log
from MaKaC.webinterface.rh.base import RH
from MaKaC.errors import MaKaCError
from indico.core.config import Config
from MaKaC.conference import LocalFile,Link,Category
from MaKaC.export import fileConverter
from MaKaC.conference import Conference,Session,Contribution,SubContribution
from MaKaC.i18n import _
from MaKaC.user import AvatarHolder, GroupHolder

from MaKaC.common.logger import Logger
from MaKaC.common.timezoneUtils import nowutc

from indico.util import json
from indico.util.contextManager import ContextManager

BYTES_1MB = 1024 * 1024


class RHCustomizable(RH):

    def __init__(self, req=None):
        RH.__init__(self)
        self._wf = ""

    def getWebFactory( self ):
        if self._wf == "":
            wr = webFactoryRegistry.WebFactoryRegistry()
            self._wf = wr.getFactory( self._conf )
        return self._wf


class RHConferenceSite( RHCustomizable ):

    def _checkParams( self, params ):
        l = locators.WebLocator()
        l.setConference( params )
        self._conf = self._target = l.getObject()
        ContextManager.set("currentConference", self._conf)

    def _getLoginURL(self, return_url=None):
        url = return_url or self.getRequestURL()
        if url == "":
            url = urlHandlers.UHConferenceDisplay.getURL( self._conf )
        wr = webFactoryRegistry.WebFactoryRegistry()
        self._wf = wr.getFactory( self._conf )
        if self._wf is not None or self._conf is None:
            return urlHandlers.UHSignIn.getURL( url )
        else:
            return urlHandlers.UHConfSignIn.getURL( self._target, url )



class RHConferenceBase( RHConferenceSite ):
    pass


class RHSessionBase( RHConferenceSite ):

    def _checkParams( self, params ):
        l = locators.WebLocator()
        l.setSession( params )
        self._session = self._target = l.getObject()
        self._conf = self._session.getConference()

class RHSessionSlotBase( RHConferenceSite ):

    def _checkParams( self, params ):
        l = locators.WebLocator()
        l.setSlot( params )
        self._slot = self._target = l.getObject()
        self._session = self._slot.getSession()
        self._conf = self._session.getConference()


class RHContributionBase( RHConferenceSite ):

    def _checkParams( self, params ):
        l = locators.WebLocator()
        l.setContribution( params )
        self._contrib = self._target = l.getObject()
        self._conf = self._contrib.getConference()

class RHSubContributionBase( RHConferenceSite ):

    def _checkParams( self, params ):
        l = locators.WebLocator()
        l.setSubContribution( params )
        self._subContrib = self._target = l.getObject()
        self._contrib = self._subContrib.getParent()
        self._conf = self._contrib.getConference()


class RHMaterialBase( RHConferenceSite ):

    def _checkParams( self, params ):
        l = locators.WebLocator()
        l.setMaterial( params )
        self._material = self._target = l.getObject()
        if self._material is None:
            raise MaKaCError( _("The material you are trying to access does not exist or was removed"))
        self._conf = self._material.getConference()
        if self._conf == None:
            self._categ=self._material.getCategory()


class RHFileBase( RHConferenceSite ):

    def _checkParams( self, params ):
        l = locators.WebLocator()
        l.setResource( params )
        self._file = self._target = l.getObject()
#        if not isinstance(self._file, LocalFile):
#            raise MaKaCError("No file found, %s found instead"%type(self._file))
        self._conf = self._file.getConference()
        if self._conf == None:
            self._categ = self._file.getCategory()


class RHAlarmBase( RHConferenceSite ):

    def _checkParams( self, params ):
        l = locators.WebLocator()
        l.setAlarm( params )
        self._alarm = self._target = l.getObject()
        self._conf = self._alarm.getConference()


class RHLinkBase( RHConferenceSite ):

    def _checkParams( self, params ):
        l = locators.WebLocator()
        l.setResource( params )
        self._link = self._target = l.getObject()
        self._conf = self._link.getConference()
        if self._conf == None:
            self._categ=self._link.getCategory()


class RHTrackBase( RHConferenceSite ):

    def _checkParams( self, params ):
        l = locators.WebLocator()
        l.setTrack( params )
        self._track = self._target = l.getObject()
        self._conf = self._track.getConference()
        self._subTrack = None
        if params.has_key("subTrackId"):
            self._subTrack = self._track.getSubTrackById(params["subTrackId"])


class RHAbstractBase( RHConferenceSite ):

    def _checkParams( self, params ):
        l = locators.WebLocator()
        l.setAbstract( params )
        self._abstract = self._target = l.getObject()
        if self._abstract is None:
            raise MaKaCError( _("The abstract you are trying to access does not exist"))
        self._conf = self._abstract.getOwner().getOwner()

class RHSubmitMaterialBase(object):

    def __init__(self):
        self._tempFiles = {}
        self._repositoryIds = None
        self._errorList = []
        self._cfg = Config.getInstance()

    def _getNewTempFile( self ):
        cfg = Config.getInstance()
        tempPath = cfg.getUploadedFilesTempDir()
        tempFileName = tempfile.mkstemp(suffix="Indico.tmp", dir=tempPath)[1]
        return tempFileName

    #XXX: improve routine to avoid saving in temporary file
    def _saveFileToTemp(self, fs):
        if fs not in self._tempFiles:
            fileName = self._getNewTempFile()
            fs.save(fileName)
            self._tempFiles[fs] = fileName
            self._tempFilesToDelete.append(fileName)
        return self._tempFiles[fs]

    def _checkProtection(self):
        self._loggedIn = True
        if self._getUser() == None and (isinstance(self._target, Category) or not self._target.getConference().canKeyModify(self._aw)):
            self._loggedIn = False
        elif self._getUser() and isinstance(self._target, Conference) and self._target.getAccessController().canUserSubmit(self._getUser()):
            self._loggedIn = True
        else:
            super(RHSubmitMaterialBase, self)._checkProtection()

    def _checkParams(self,params):

        self._params = params
        self._action = ""
        self._overwrite = False
        #if request has already been handled (DB conflict), then we keep the existing files list

        self._files = []
        self._links = []
        self._topdf = "topdf" in params

        self._displayName = params.get("displayName", "").strip()
        self._uploadType = params.get("uploadType", "")
        self._materialId = params.get("materialId", "")
        self._description = params.get("description", "")
        self._statusSelection = int(params.get("statusSelection", 1))
        self._visibility = int(params.get("visibility", 0))
        self._password = params.get("password", "")
        self._doNotSanitizeFields.append("password")

        self._userList = json.loads(params.get("userList", "[]"))
        maxUploadFilesTotalSize = float(self._cfg.getMaxUploadFilesTotalSize())

        if self._uploadType == "file":
            if isinstance(params["file"], list):
                files = params["file"]
                self._displayName = ""
                self._description = ""
            else:
                files = [params["file"]]

            for fileUpload in files:
                if type(fileUpload) != str and fileUpload.filename.strip() != "":
                    fDict = {}

                    fDict["fileName"] = fileUpload.filename.encode("utf-8")
                    estimSize = request.content_length

                    if maxUploadFilesTotalSize and estimSize > (maxUploadFilesTotalSize * BYTES_1MB):
                        # if file is too big, do not save it in disk
                        fDict["filePath"] = ''
                        fDict["size"] = estimSize
                    else:
                        fDict["filePath"] = self._saveFileToTemp(fileUpload)
                        fDict["size"] = os.path.getsize(fDict["filePath"])

                    self._setErrorList(fDict)
                    self._files.append(fDict)

        elif self._uploadType == "link":
            if isinstance(params["url"], list):
                urls = params["url"]
                self._displayName = ""
                self._description = ""
            else:
                urls = [params["url"]]

            matType = params.get("materialType", "")
            for url in urls:
                if not url.strip():
                    continue
                link = {}
                link["url"] = url
                link["matType"] = matType
                self._links.append(link)


    def _setErrorList(self, fileEntry):
        maxUploadFilesTotalSize = float(self._cfg.getMaxUploadFilesTotalSize())
        if self._uploadType == "file":
            if "filePath" in fileEntry and not fileEntry["filePath"].strip():
                self._errorList.append(_("""A valid file to be submitted must be specified. """))
            if "size" in fileEntry:
                if fileEntry["size"] < 10:
                    self._errorList.append(_("""The file %s seems to be empty """) % fileEntry["fileName"])
                elif maxUploadFilesTotalSize and fileEntry["size"] > (maxUploadFilesTotalSize*1024*1024):
                    self._errorList.append(_("The file size of %s exceeds the upload limit (%s Mb)") % (fileEntry["fileName"], maxUploadFilesTotalSize))
        elif self._uploadType == "link":
            if not self._links[0]["url"].strip():
                self._errorList.append(_("""A valid URL must be specified."""))

        if self._materialId=="":
            self._errorList.append(_("""A material ID must be selected."""))

    def _getMaterial(self, forceCreate = True):
        """
        Returns the Material object to which the resource is being added
        """

        registry = self._target.getMaterialRegistry()
        material = self._target.getMaterialById(self._materialId)

        if material:
            return material, False
        # there's a defined id (not new type)
        elif self._materialId:
            # get a material factory for it
            mf = registry.getById(self._materialId)
            # get a material from the material factory
            material = mf.get(self._target)

            # if the factory returns an empty material (doesn't exist)
            if material == None and forceCreate:
                # create one
                material = mf.create(self._target)
                newlyCreated = True
            else:
                newlyCreated = False

            return material, newlyCreated
        else:
            # else, something has gone wrong
            raise Exception("""A material ID must be specified.""")

    def _addMaterialType(self, text, user):

        from MaKaC.common.fossilize import fossilize
        from MaKaC.fossils.conference import ILocalFileExtendedFossil, ILinkFossil

        Logger.get('requestHandler').debug('Adding %s - request %s' % (self._uploadType, request))

        mat, newlyCreated = self._getMaterial()

        # if the material still doesn't exist, create it
        if newlyCreated:
            protectedAtResourceLevel = False
        else:
            protectedAtResourceLevel = True

        resources = []
        if self._uploadType in ['file','link']:
            if self._uploadType == "file":
                for fileEntry in self._files:
                    resource = LocalFile()
                    resource.setFileName(fileEntry["fileName"])
                    resource.setFilePath(fileEntry["filePath"])
                    resource.setDescription(self._description)
                    if self._displayName == "":
                        resource.setName(resource.getFileName())
                    else:
                        resource.setName(self._displayName)

                    if not type(self._target) is Category:
                        log_info = {"subject":"Added file %s%s" % (fileEntry["fileName"], text)}
                        self._target.getConference().getLogHandler().logAction(log_info, log.ModuleNames.MATERIAL)
                    resources.append(resource)
                    # in case of db conflict we do not want to send the file to conversion again, nor re-store the file

            elif self._uploadType == "link":

                for link in self._links:
                    resource = Link()
                    resource.setURL(link["url"])
                    resource.setDescription(self._description)
                    if self._displayName == "":
                        resource.setName(resource.getURL())
                    else:
                        resource.setName(self._displayName)

                    if not type(self._target) is Category:
                        log_info = {"subject":"Added link %s%s" % (resource.getURL(), text)}
                        self._target.getConference().getLogHandler().logAction(log_info, log.ModuleNames.MATERIAL)
                    resources.append(resource)

            status = "OK"
            info = resources
        else:
            status = "ERROR"
            info = "Unknown upload type"
            return mat, status, info

        # forcedFileId - in case there is a conflict, use the file that is
        # already stored
        repoIDs = []
        for i, resource in enumerate(resources):
            if self._repositoryIds:
                mat.addResource(resource, forcedFileId=self._repositoryIds[i])
            else:
                mat.addResource(resource, forcedFileId=None)

            #apply conversion
            if self._topdf and not isinstance(resource, Link):
                file_ext = os.path.splitext(resource.getFileName())[1].strip().lower()
                if fileConverter.CDSConvFileConverter.hasAvailableConversionsFor(file_ext):
                    # Logger.get('conv').debug('Queueing %s for conversion' % resource.getFilePath())
                    fileConverter.CDSConvFileConverter.convert(resource.getFilePath(), 'pdf', mat)
                    resource.setPDFConversionRequestDate(nowutc())

            # store the repo id, for files
            if isinstance(resource, LocalFile) and self._repositoryIds is None:
                repoIDs.append(resource.getRepositoryId())

            if protectedAtResourceLevel:
                protectedObject = resource
            else:
                protectedObject = mat
                mat.setHidden(self._visibility)
                mat.setAccessKey(self._password)

                protectedObject.setProtection(self._statusSelection)

            for userElement in self._userList:
                if 'isGroup' in userElement and userElement['isGroup']:
                    avatar = GroupHolder().getById(userElement['id'])
                else:
                    avatar = AvatarHolder().getById(userElement['id'])
                protectedObject.grantAccess(avatar)

        self._topdf = False
        if self._repositoryIds is None:
            self._repositoryIds = repoIDs

        return mat, status, fossilize(info, {"MaKaC.conference.Link": ILinkFossil,
                                             "MaKaC.conference.LocalFile": ILocalFileExtendedFossil})

    def _process(self):
        # We will need to pickle the data back into JSON

        user = self.getAW().getUser()

        if not self._loggedIn:
            return json.dumps({
                'status': 'ERROR',
                'info': {
                    'type': 'noReport',
                    'title': '',
                    'explanation': _('You are currently not authenticated. Please log in again.')
                }
            }, textarea=True)

        try:
            owner = self._target
            title = owner.getTitle()
            if type(owner) == Conference:
                ownerType = "event"
            elif type(owner) == Session:
                ownerType = "session"
            elif type(owner) == Contribution:
                ownerType = "contribution"
            elif type(owner) == SubContribution:
                ownerType = "subcontribution"
            else:
                ownerType = ""
            text = " in %s %s" % (ownerType,title)
        except:
            owner = None
            text = ""

        try:
            if len(self._errorList) > 0:
                raise Exception('Operation aborted')
            else:
                mat, status, info = self._addMaterialType(text, user)

                if status == "OK":
                    for entry in info:
                        entry['material'] = mat.getId()
        except Exception, e:
            status = "ERROR"
            if 'file' in self._params:
                del self._params['file']
            info = {'message': self._errorList or " %s: %s" % (e.__class__.__name__, str(e)),
                    'code': '0',
                    'requestInfo': self._params}
            Logger.get('requestHandler').exception('Error uploading file')
        return json.dumps({'status': status, 'info': info}, textarea=True)

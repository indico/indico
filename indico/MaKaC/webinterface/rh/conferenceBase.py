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
import os
import MaKaC.webinterface.locators as locators
import MaKaC.webinterface.webFactoryRegistry as webFactoryRegistry
from MaKaC.paperReviewing import reviewing_factory_get, reviewing_factory_create
from MaKaC.webinterface.rh.base import RH
from MaKaC.errors import MaKaCError, NotFoundError
from indico.core.config import Config
from MaKaC.conference import LocalFile, Category
from MaKaC.conference import Conference, Session, Contribution, SubContribution
from MaKaC.i18n import _

from indico.core.errors import IndicoError
from indico.core.logger import Logger

from indico.util import json
from indico.util.contextManager import ContextManager
from indico.util.string import is_legacy_id
from indico.util.user import principal_from_fossil

BYTES_1MB = 1024 * 1024


class RHCustomizable(RH):

    def __init__(self):
        RH.__init__(self)
        self._wf = ""

    def getWebFactory( self ):
        if self._wf == "":
            wr = webFactoryRegistry.WebFactoryRegistry()
            self._wf = wr.getFactory( self._conf )
        return self._wf


class RHConferenceSite(RHCustomizable):
    ALLOW_LEGACY_IDS = True

    def _legacy_check(self):
        if self.ALLOW_LEGACY_IDS:
            return
        event_id = request.view_args.get('confId') or request.values.get('confId')
        if event_id is not None and is_legacy_id(event_id):
            raise IndicoError('This page is not available for legacy events.')

    def _checkParams(self, params):
        l = locators.WebLocator()
        l.setConference( params )
        self._conf = self._target = l.getObject()
        ContextManager.set("currentConference", self._conf)


class RHConferenceBase( RHConferenceSite ):
    pass


class RHSessionBase( RHConferenceSite ):

    def _checkParams( self, params ):
        l = locators.WebLocator()
        l.setSession( params )
        self._session = self._target = l.getObject()
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


class RHFileBase(RHConferenceSite):

    def _checkParams(self, params):
        l = locators.WebLocator()
        l.setResource(params)
        self._file = self._target = l.getObject()
#        if not isinstance(self._file, LocalFile):
#            raise MaKaCError("No file found, %s found instead"%type(self._file))
        self._conf = self._file.getConference()
        if self._conf is None:
            self._categ = self._file.getCategory()


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
        if (self._getUser() is None and (isinstance(self._target, Category) or
                                         not self._target.getConference().canKeyModify())):
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

        self._displayName = params.get("displayName", "").strip()
        self._uploadType = params.get("uploadType", "")
        self._materialId = params.get("materialId", "")
        assert self._materialId == 'reviewing'
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

    def _getMaterial(self, forceCreate=True):
        """
        Returns the Material object to which the resource is being added
        """
        assert self._materialId == 'reviewing'  # only reviewing still uses this...
        material = reviewing_factory_get(self._target)
        if material is None and forceCreate:
            material = reviewing_factory_create(self._target)
            newlyCreated = True
        else:
            newlyCreated = False

        return material, newlyCreated

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
        assert self._uploadType == "file"
        for fileEntry in self._files:
            resource = LocalFile()
            resource.setFileName(fileEntry["fileName"])
            resource.setFilePath(fileEntry["filePath"])
            resource.setDescription(self._description)
            if self._displayName == "":
                resource.setName(resource.getFileName())
            else:
                resource.setName(self._displayName)
            resources.append(resource)
        status = "OK"
        info = resources

        # forcedFileId - in case there is a conflict, use the file that is
        # already stored
        repoIDs = []
        for i, resource in enumerate(resources):
            if self._repositoryIds:
                mat.addResource(resource, forcedFileId=self._repositoryIds[i])
            else:
                mat.addResource(resource, forcedFileId=None)

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

            for principal in map(principal_from_fossil, self._userList):
                protectedObject.grantAccess(principal)

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

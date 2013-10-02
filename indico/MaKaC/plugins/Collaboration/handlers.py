# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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
Request handlers for Collaboration plugins
"""

# standard lib imports
import os, tempfile, time
import pkg_resources
# legacy indico imports

# indico api imports
from indico.util import json
from indico.web.rh import RHHtdocs
from MaKaC.webinterface.rh.collaboration import RHConfModifCSBookings
from MaKaC.webinterface.rh.conferenceBase import RHConferenceBase
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.plugins import Collaboration
from MaKaC.plugins.Collaboration.base import SpeakerStatusEnum
from MaKaC.plugins.Collaboration.pages import WPElectronicAgreement, WPElectronicAgreementForm, WPElectronicAgreementFormConference
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.errors import MaKaCError
from MaKaC.conference import LocalFile
from MaKaC.webinterface.common.tools import cleanHTMLHeaderFilename
from MaKaC.webinterface.urlHandlers import URLHandler
from MaKaC.common.logger import Logger
from MaKaC.common import Config


class RHElectronicAgreement(RHConfModifCSBookings):
    _url = r'^/Collaboration/elecAgree/?$'

    def _checkParams(self, params):
        RHConfModifCSBookings._checkParams(self, params)
        self._activeTabName = 'Electronic Agreement'
        self.sortCriteria = params.get('sortBy', 'speaker')
        self.order = params.get('order', 'down')

    def _process(self):
        if self._cannotViewTab:
            raise MaKaCError(_("That Video Services tab doesn't exist"), _("Video Services"))
        else:
            p = WPElectronicAgreement(self, self._conf)
            return p.display(sortCriteria=self.sortCriteria, order=self.order)


class RHUploadElectronicAgreement(RHConferenceModifBase):
    _url = r'^/Collaboration/uploadElecAgree/?$'

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.spkUniqueId = params.get('spkUniqueId', None)
        self.file = params.get('file', None)
        self.filePath = ''

        if self.file and self.spkUniqueId:
            try:
                self.filePath = self.saveFileToTemp(self.file.file)
                self._tempFilesToDelete.append(self.filePath)
            except AttributeError:
                raise MaKaCError("Problem when storing file")

    def getNewTempFile( self ):
        cfg = Config.getInstance()
        tempPath = cfg.getUploadedFilesTempDir()
        tempFileName = tempfile.mkstemp( suffix="IndicoFileUpload.tmp", dir = tempPath )[1]
        return tempFileName

    def saveFileToTemp( self, fd ):
        fileName = self.getNewTempFile()
        f = open( fileName, "wb" )
        f.write( fd.read() )
        f.close()
        return fileName

    def uploadProcess(self):
        # We save the file
        try:
            f = LocalFile()
            __, extension = os.path.splitext(self.file.filename)
            f.setFileName("EAForm-{0}{1}".format(self.spkUniqueId, extension))
            f.setFilePath(self.filePath)
            f.setId(self.spkUniqueId)
            # Update status for speaker wrapper
            manager = self._conf.getCSBookingManager()
            spkWrapper = manager.getSpeakerWrapperByUniqueId(self.spkUniqueId)
            repo = self._conf._getRepository()

            f.setOwner(spkWrapper)
            f.archive(repo)
            # if no error, update the speaker wrapper...
            spkWrapper.setStatus(SpeakerStatusEnum.FROMFILE) #change status
            spkWrapper.setLocalFile(f) # set path to file
            spkWrapper.triggerNotification() # trigger notification task
        except:
            Logger.get('file_upload').exception("Error uploading file")
            raise MaKaCError("Unexpected error while uploading file")

    def _process(self):
        if self.spkUniqueId and self.file:
            self.uploadProcess()
            return json.dumps({'status': 'OK'}, textarea=True)

class RHElectronicAgreementGetFile(RHConfModifCSBookings):
    _url = r'^/Collaboration/getPaperAgree/?$'

    def _checkParams(self, params):
        RHConfModifCSBookings._checkParams( self, params )
        self.spkUniqueId = params.get("spkId","")

    def _process(self):
        manager = self._conf.getCSBookingManager()
        sw = manager.getSpeakerWrapperByUniqueId(self.spkUniqueId)
        if sw:
            self.file = sw.getLocalFile()
            self._req.headers_out["Content-Length"] = "%s"%self.file.getSize()
            self._req.headers_out["Last-Modified"] = "%s"%time.mktime(self.file.getCreationDate().timetuple())
            cfg = Config.getInstance()
            mimetype = cfg.getFileTypeMimeType( self.file.getFileType() )
            print self.file.getFilePath()
            self._req.content_type = """%s"""%(mimetype)
            dispos = "inline"
            try:
                if self._req.headers_in['User-Agent'].find('Android') != -1:
                    dispos = "attachment"
            except KeyError:
                pass
            self._req.headers_out["Content-Disposition"] = '%s; filename="%s"' % (dispos, cleanHTMLHeaderFilename(self.file.getFileName()))

            if cfg.getUseXSendFile():
                # X-Send-File support makes it easier, just let the web server
                # do all the heavy lifting
                return self._req.send_x_file(self.file.getFilePath())
            else:
                return self.file.readBin()
        else:
            raise MaKaCError("The speaker wrapper id does not match any existing speaker.")


class RHElectronicAgreementForm(RHConferenceBase):
    _url = r'^/Collaboration/elecAgreeForm/?$'

    def _checkParams(self, params):
        RHConferenceBase._checkParams(self, params)
        self.authKey = params['authKey']

    def _process(self):
        return self.wpEvaluation()

    def wpEvaluation(self):
        wf = self.getWebFactory()
        if wf !=None: # Event: Meeting/Lecture
            return WPElectronicAgreementForm(self, self._conf, self.authKey).display()
        else:# Event: Conference
            return WPElectronicAgreementFormConference(self, self._conf, self.authKey).display()


class UHCollaborationHtdocs(URLHandler):
    """
    URL handler for epayment status
    """
    _relativeURL = "Collaboration"


class RHCollaborationHtdocs(RHHtdocs):
    """
    Static file handler for Collaboration plugin
    """

    _url = r"^/Collaboration/(?:(?P<plugin>[^\s/]+)/)?(?P<filepath>[^\s/]+)$"

    @classmethod
    def calculatePath(cls, plugin, filepath):

        if plugin:
            module = CollaborationTools.getModule(plugin)
            if module:
                local_path = pkg_resources.resource_filename(module.__name__, "")
            else:
                return None
        else:
            local_path = pkg_resources.resource_filename(Collaboration.__name__, "")

        return super(RHCollaborationHtdocs, cls).calculatePath(
            filepath,
            local_path=os.path.join(local_path, 'htdocs'))

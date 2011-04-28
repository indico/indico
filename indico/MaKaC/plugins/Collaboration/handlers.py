# -*- coding: utf-8 -*-
##
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

"""
Request handlers for Collaboration plugins
"""

# standard lib imports
import os, tempfile, time

# legacy indico imports

# indico api imports
from indico.web.rh import RHHtdocs
from MaKaC.webinterface.rh.collaboration import RHConfModifCSBookings
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
from MaKaC.plugins.Collaboration.pages import *
from MaKaC.webinterface.pages.conferences import WPConferenceModificationClosed
from MaKaC.plugins.base import PluginsHolder
from MaKaC.errors import MaKaCError
from MaKaC.conference import LocalFile
import MaKaC.webinterface.displayMgr as displayMgr

AGREEMENTPATH = "/home/gcerto/Desktop/EAForms"

class RHCollaborationElectronicAgreement(RHConfModifCSBookings):
    _url = r'^/Collaboration/elecAgree/?$'

    def _checkParams(self, params):
        RHConfModifCSBookings._checkParams(self, params)
        self._activeTabName = 'Electronic Agreement'
        self.sortCriteria = params.get('sortBy', 'speaker')
        self.order = params.get('order', 'down')

        #If this is an upload
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
            f.setFileName("EAForm-%s"%self.spkUniqueId)
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
        except:
            raise MaKaCError("Unexpected error while uploading file")


    def _process(self):
        if self.spkUniqueId and self.file:
            self.uploadProcess()

        ph = PluginsHolder()
        if ph.getPluginType('Collaboration').getOption("useHTTPS").getValue():
            self._tohttps = True
            if self._checkHttpsRedirect():
                return ""

        if self._cannotViewTab:
            raise MaKaCError(_("That Video Services tab doesn't exist"), _("Video Services"))
        else:
            p = WPCollaborationElectronicAgreement(self, self._conf)
            return p.display(sortCriteria = self.sortCriteria, order = self.order)

class RHCollaborationElectronicAgreementGetFile(RHConferenceBaseDisplay):
    _url = r'^/Collaboration/getPaperAgree/?$'

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams( self, params )
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
            self._req.content_type = """%s"""%(mimetype)
            dispos = "inline"
            try:
                if self._req.headers_in['User-Agent'].find('Android') != -1:
                    dispos = "attachment"
            except KeyError:
                pass
            self._req.headers_out["Content-Disposition"] = '%s; filename="%s"' % (dispos, self.file.getFileName())

            if cfg.getUseXSendFile():
                # X-Send-File support makes it easier, just let the web server
                # do all the heavy lifting
                return self._req.send_x_file(self.file.getFilePath())
            else:
                return self.file.readBin()
        else:
            raise MaKaCError("The speaker wrapper id does not match any existing speaker.")

class RHCollaborationElectronicAgreementForm(RHConferenceBaseDisplay):
    _url = r'^/Collaboration/elecAgreeForm/?$'

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.authKey = params['authKey']

    def _process(self):
        return self.wpEvaluation()

    def wpEvaluation(self):
        wf = self.getWebFactory()
        if wf !=None: # Event: Meeting/Lecture
            return WPCollaborationElectronicAgreementForm(self, self._conf, self.authKey).display()
        else:# Event: Conference
            return WPCollaborationElectronicAgreementFormConference(self, self._conf, self.authKey).display()

class RHCollaborationHtdocs(RHHtdocs):
    """
    Static file handler for Collaboration plugin
    """

    _url = r"^/Collaboration/?(?P<plugin>.*?)/(?P<filepath>.*)$"

    @classmethod
    def calculatePath(cls, plugin, filepath):
        ''' Changed this function to accept also the case where no <plugin>
        '''
        if plugin:
            module = CollaborationTools.getModule(plugin)
            if module:
                return os.path.join(module.__path__[0],
                                    'htdocs', filepath)
            else:
                return None
        else:
            return os.path.join(Collaboration.__path__[0], 'htdocs', filepath)
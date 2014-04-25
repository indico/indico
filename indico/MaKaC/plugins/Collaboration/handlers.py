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

"""
Request handlers for Collaboration plugins
"""

# standard lib imports
import os, tempfile, time
# legacy indico imports

# indico api imports
from werkzeug.exceptions import NotFound
from indico.util import json
from indico.web.flask.util import send_file
from indico.web.handlers import RHHtdocs
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
from MaKaC.plugins.Collaboration.base import SpeakerStatusEnum
from MaKaC.conference import LocalFile
from MaKaC.common.logger import Logger
from MaKaC.webinterface.rh.base import RoomBookingDBMixin
from MaKaC.webinterface.rh.conferenceBase import RHConferenceBase
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from indico.core.index import Catalog
from MaKaC.plugins import PluginsHolder, Plugin
from MaKaC.errors import MaKaCError
from MaKaC.webinterface.pages import conferences
from MaKaC.i18n import _
from MaKaC.webinterface.rh.admins import RCAdmin, RHAdminBase
from MaKaC.user import Group, Avatar
from MaKaC.plugins.Collaboration.pages import WPAdminCollaboration, WPCollaborationDisplay, \
    WPConfModifCollaboration, WPConfModifCollaborationProtection, WPElectronicAgreementFormConference, \
    WPElectronicAgreementForm, WPElectronicAgreement
from indico.core.config import Config


class RCCollaborationAdmin(object):
    @staticmethod
    def hasRights(user):
        """ Returns True if the user is a Server Admin or a Collaboration admin
            user: an Avatar object
        """

        if user:
            # check if user is Server Admin, Collaboration Admin
            collaborationAdmins = PluginsHolder().getPluginType('Collaboration').getOption('collaborationAdmins').getValue()
            return RCAdmin.hasRights(None, user) or user in collaborationAdmins
        return False


class RCCollaborationPluginAdmin(object):
    @staticmethod
    def hasRights(user, plugins=[]):
        """ Returns True if the user is an admin of one of the plugins corresponding to pluginNames
            plugins: a list of Plugin objects (e.g. EVO, RecordingRequest) or strings with the plugin name ('EVO', 'RecordingRequest')
                     or the string 'any' (we will then check if the user is manager of any plugin),
        """
        if user:
            plist = CollaborationTools.getCollaborationPluginType().getPluginList() if plugins == 'any' else plugins

            if plist:
                for plugin in plist:
                    if not isinstance(plugin, Plugin):
                        plugin = CollaborationTools.getPlugin(plugin)
                    if user in plugin.getOption('admins').getValue():
                        return True
        return False


class RCVideoServicesManager(object):
    @staticmethod
    def hasRights(user, conf, plugins=[]):
        """ Returns True if the logged in user has rights to operate with bookings of at least one of a list of plugins, for an event.
            This is true if:
                -the user is a Video Services manager (can operate with all plugins)
                -the user is a plugin manager of one of the plugins
            Of course, it's also true if the user is event manager or server admin, but this class does not cover that case.

            request: an RH or Service object
            plugins: either a list of plugin names, or Plugin objects (we will then check if the user is manager of any of those plugins),
                     or the string 'any' (we will then check if the user is manager of any plugin),
                     or nothing (we will then check if the user is a Video Services manager).
        """

        if user:
            csbm = Catalog.getIdx("cs_bookingmanager_conference").get(conf.getId())
            if csbm.isVideoServicesManager(user):
                return True

            plugins = plugins
            if plugins == 'any':
                return csbm.isPluginManagerOfAnyPlugin(user)

            for plugin in plugins:
                if isinstance(plugin, Plugin):
                    plugin = plugin.getName()
                if csbm.isPluginManager(plugin, user):
                    return True
        return False


class RCVideoServicesUser(object):
    @staticmethod
    def hasRights(user, pluginName=""):
        """ Returns True if the logged in user is an authorised user to create bookings.
            This is true if:
                  - The user is in the list of authorised user and groups
            request: the user
            pluginName: the plugin to check
        """
        if user:
            plugin = CollaborationTools.getPlugin(pluginName)
            if plugin.hasOption("AuthorisedUsersGroups"):
                if plugin.getOption("AuthorisedUsersGroups").getValue():
                    for entity in plugin.getOption("AuthorisedUsersGroups").getValue():
                        if isinstance(entity, Group) and entity.containsUser(user) or \
                            isinstance(entity, Avatar) and entity == user:
                                return True
                    return False
                else:
                    return True
            else:
                return True
        return False

################################################### Event Modification Request Handlers ####################################
class RHConfModifCSBase(RHConferenceModifBase):
    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)

        self._activeTabName = params.get("tab", None)

        # we build the list 'allowedTabs', a list of all tabs that the user can see
        allowedTabs = CollaborationTools.getTabs(self._conf, self._getUser())

        if self._target.canModify(self.getAW()) or RCVideoServicesManager.hasRights(self._getUser(), self._conf):
            allowedTabs.append('Managers')

        tabOrder = CollaborationTools.getCollaborationOptionValue('tabOrder')
        self._tabs = []

        for tabName in tabOrder:
            if tabName in allowedTabs:
                self._tabs.append(tabName)
                allowedTabs.remove(tabName)

        for tabName in allowedTabs:
            if tabName != 'Managers':
                self._tabs.append(tabName)

        if 'Managers' in allowedTabs:
            self._tabs.append('Managers')


class RHConfModifCSBookings(RoomBookingDBMixin, RHConfModifCSBase):
    _tohttps = True

    def _checkParams(self, params):
        RHConfModifCSBase._checkParams(self, params)

        if self._activeTabName and not self._activeTabName in self._tabs:
            self._cannotViewTab = True
        else:
            self._cannotViewTab = False
            if not self._activeTabName and self._tabs:
                self._activeTabName = self._tabs[0]

            self._tabPlugins = CollaborationTools.getPluginsByTab(self._activeTabName, self._conf, self._getUser())

    def _checkProtection(self):
        self._checkSessionUser()

        hasRights = (not self._cannotViewTab) and \
                    (RCCollaborationAdmin.hasRights(self._getUser()) or
                     RCCollaborationPluginAdmin.hasRights(self._getUser(), self._tabPlugins) or
                     RCVideoServicesManager.hasRights(self._getUser(), self._conf, self._tabPlugins) )

        if not hasRights:
            RHConferenceModifBase._checkProtection(self)

    def _process( self ):

        if self._conf.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display()
        else:
            if self._cannotViewTab:
                raise MaKaCError(_("That Video Services tab doesn't exist"), _("Video Services"))
            else:
                p = WPConfModifCollaboration( self, self._conf)
                return p.display()

class RHConfModifCSProtection(RHConfModifCSBase):

    def _checkParams(self, params):
        RHConfModifCSBase._checkParams(self, params)
        self._activeTabName = 'Managers'

    def _checkProtection(self):

        if not RCVideoServicesManager.hasRights(self._getUser(), self._conf):
            RHConferenceModifBase._checkProtection(self)

    def _process( self ):

        if self._conf.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display()
        else:
            p = WPConfModifCollaborationProtection( self, self._conf)
            return p.display()


class RHElectronicAgreement(RHConfModifCSBookings):
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
            manager = Catalog.getIdx("cs_bookingmanager_conference").get(self._conf.getId())
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
    def _checkParams(self, params):
        RHConfModifCSBookings._checkParams( self, params )
        self.spkUniqueId = params.get("spkId","")

    def _process(self):
        manager = Catalog.getIdx("cs_bookingmanager_conference").get(self._conf.getId())
        sw = manager.getSpeakerWrapperByUniqueId(self.spkUniqueId)
        if not sw:
            raise MaKaCError("The speaker wrapper id does not match any existing speaker.")
        self.file = sw.getLocalFile()
        return send_file(self.file.getFileName(), self.file.getFilePath(), self.file.getFileType(),
                         self.file.getCreationDate())


class RHElectronicAgreementForm(RHConferenceBase):
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

################################################### Server Wide pages #########################################
class RHAdminCollaboration(RHAdminBase):

    def _checkParams( self, params ):
        RHAdminBase._checkParams( self, params )
        self._queryParams = {}
        self._queryParams["queryOnLoad"] = (params.get('queryOnLoad', None) == 'true')
        self._queryParams["page"] = params.get("page", 1)
        self._queryParams["resultsPerPage"] = params.get("resultsPerPage", 10)
        self._queryParams["indexName"] = params.get('indexName', None)
        self._queryParams["viewBy"] = params.get('viewBy', 'startDate')
        self._queryParams["orderBy"] = params.get('orderBy', '')
        self._queryParams["sinceDate"] = params.get('fromDate', '').strip()
        self._queryParams["toDate"] = params.get('toDate', '').strip()
        self._queryParams["fromDays"] = params.get('fromDays', '').strip()
        self._queryParams["toDays"] = params.get('toDays', '').strip()
        self._queryParams["fromTitle"] = params.get('fromTitle', '').strip()
        self._queryParams["toTitle"] = params.get('toTitle', '').strip()
        self._queryParams["onlyPending"] = (params.get('onlyPending', None) == 'true')
        self._queryParams["conferenceId"] = params.get('conferenceId', '').strip()
        self._queryParams["categoryId"] = params.get('categoryId', '').strip()

    def _checkProtection( self ):

        if not RCCollaborationAdmin.hasRights(self._getUser()) and \
           not RCCollaborationPluginAdmin.hasRights(self._getUser(), plugins="any"):
            RHAdminBase._checkProtection(self)

    def _process(self):
        p = WPAdminCollaboration( self , self._queryParams)
        return p.display()


################################################### Event Display Request Handlers ####################################
class RHCollaborationDisplay(RHConferenceBaseDisplay):

    def _process( self ):
        p = WPCollaborationDisplay( self, self._target )
        return p.display()

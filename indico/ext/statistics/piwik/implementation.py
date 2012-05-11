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
import os
import indico.ext.statistics.piwik

from indico.ext.statistics.base.implementation import BaseStatisticsImplementation, JSHookBase

from MaKaC.plugins.base import PluginsHolder
from MaKaC.i18n import _
from MaKaC.webinterface.urlHandlers import UHFileAccess


class PiwikStatisticsImplementation(BaseStatisticsImplementation):

    QUERY_SCRIPT = 'piwik.php'
    QUERY_KEY_NAME = 'token_auth'

    _name = 'Piwik'

    def __init__(self):
        BaseStatisticsImplementation.__init__(self)
        self._implementationPackage = indico.ext.statistics.piwik
        self._APISegmentation = []
        self._setHasJSHook(True)
        self._setHasDownloadListener(True)

        self.setAPIToken(self._getSavedAPIToken())
        self.setAPISiteID(self._getSavedAPISiteID())

    def _buildPluginPath(self):
        """
        Local, absolute location of plugin.
        """
        self._FSPath = os.path.join(indico.ext.statistics.piwik.__path__)[0]

    @staticmethod
    def getVarFromPluginStorage(varName):
        """
        Retrieves varName from the options of the plugin.
        """
        piwik = PluginsHolder().getPluginType('statistics').getPlugin('piwik')
        return piwik.getOptions()[varName].getValue()

    def _getSavedAPIPath(self):
        """
        Returns the String saved in the plugin configuration for the
        Piwik server URL.
        """
        return PiwikStatisticsImplementation.getVarFromPluginStorage('serverUrl')

    def _getSavedAPIToken(self):
        """
        Returns the String saved in the plugin configuration for the
        Piwik token auth.
        """
        return PiwikStatisticsImplementation.getVarFromPluginStorage('serverTok')

    def _getSavedAPISiteID(self):
        """
        Returns the String saved in the plugin configuration for the
        Piwik ID Site
        """
        return PiwikStatisticsImplementation.getVarFromPluginStorage('serverSiteID')

    def hasJSHook(self):
        """
        This implementation permits the JSHook & Download listener to be
        enabled/disabled separately, checks for this option first then falls
        back to default plugin activity if not disabled locally. By doing this,
        the components are not appended to the list of subsribers when listeners
        are iterating.
        """
        enabled = PiwikStatisticsImplementation.getVarFromPluginStorage('jsHookEnabled')

        return BaseStatisticsImplementation.hasJSHook(self) if enabled else False

    def hasDownloadListener(self):
        """
        Overridden method, see self.hasJSHook for explaination of logic.
        """
        enabled = PiwikStatisticsImplementation.getVarFromPluginStorage('downloadTrackingEnabled')

        return BaseStatisticsImplementation.hasDownloadListener(self) if enabled else False

    @staticmethod
    @BaseStatisticsImplementation.memoizeReport
    def getConferenceReport(startDate, endDate, confId, contribId=None):
        """
        Returns the report object which satisifies the confId given.
        """
        from indico.ext.statistics.piwik.reports import PiwikReport
        return PiwikReport(startDate, endDate, confId, contribId).fossilize()

    @staticmethod
    def getContributionReport(startDate, endDate, confId, contribId):
        """
        Returns the report object for the contribId given.
        """
        return PiwikStatisticsImplementation.getConferenceReport(startDate, endDate,
                                                                 confId, contribId)

    def getJSHookObject(self, instantiate=False):
        """
        Returns a reference to or an instance of the JSHook class.
        """
        reference = indico.ext.statistics.piwik.implementation.JSHook

        return reference() if instantiate else reference

    def setAPISiteID(self, id):
        """
        Piwik identifies sites by their 'idSite' attribute.
        """
        self.setAPIParams({'idSite': id})

    def setAPIAction(self, action):
        self.setAPIParams({'action': action})

    def setAPIInnerAction(self, action):
        self.setAPIParams({'apiAction': action})

    def setAPIMethod(self, method):
        self.setAPIParams({'method': method})

    def setAPIModule(self, module):
        self.setAPIParams({'module': module})

    def setAPIInnerModule(self, module):
        self.setAPIParams({'apiModule': module})

    def setAPIFormat(self, format='JSON'):
        self.setAPIParams({'format': format})

    def setAPIPeriod(self, period='day'):
        self.setAPIParams({'period': period})

    def setAPIDate(self, date=['last7']):
        newDate = date[0] if len(date) == 1 else ','.join(date)

        self.setAPIParams({'date': newDate})

    def setAPISegmentation(self, segmentation):
        """
        segmentation = {'key': ('equality', 'value')}
        """

        for segmentName, (equality, segmentValue) in segmentation.iteritems():
            if isinstance(segmentValue, list):
                value = ','.join(segmentValue)
            else:
                value = str(segmentValue)

            segmentBuild = segmentName + equality + value

            if segmentBuild not in self._APISegmentation:
                self._APISegmentation.append(segmentBuild)

        segmentation = self.QUERY_BREAK.join(self._APISegmentation)

        self.setAPIParams({'segment': segmentation})


    def trackDownload(self, material):
        """
        Wraps around the Piwik query object for tracking downloads, constructs
        the name by which we want to log the download and the link.
        """
        from indico.ext.statistics.piwik.queries import PiwikQueryTrackDownload
        tracker = PiwikQueryTrackDownload()

        downloadLink = str(UHFileAccess().getURL(material))
        downloadTitle = _('Download') + ' - ' + material.getFileName()

        tracker.trackDownload(downloadLink, downloadTitle)


class JSHook(JSHookBase):

    varConference = 'Conference'
    varContribution = 'Contribution'

    def __init__(self, instance, extra):
        super(JSHook, self).__init__(instance)
        self.hasConfId = self.hasContribId = False
        self._buildVars(extra)

    def _buildVars(self, item):
        """
        Builds the references to Conferences & Contributions.
        """
        self.siteId = PiwikStatisticsImplementation.getVarFromPluginStorage('serverSiteID')

        if hasattr(item, '_conf'):
            self.hasConfId = True
            self.confId = item._conf.getId()

        if hasattr(item, '_contrib'):
            self.hasContribId = True
            self.contribId = item._contrib.getUniqueId()

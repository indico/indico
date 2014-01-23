# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.

import pkg_resources
import zope.interface

import indico.ext.statistics

from indico.core.extpoint import Component
from indico.core.extpoint.events import INavigationContributor, IEventDisplayContributor, IMaterialDownloadListener
from indico.core.extpoint.plugins import IPluginSettingsContributor
from indico.ext.statistics.register import StatisticsRegister
from indico.web.handlers import RHHtdocs

from MaKaC.i18n import _
from MaKaC.errors import PluginError
from MaKaC.plugins import PluginsHolder
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.webinterface.pages.conferences import WPConferenceModifBase
from MaKaC.webinterface.urlHandlers import URLHandler
from MaKaC.webinterface import wcomponents


class StatisticsSMContributor(Component):
    """
    Adds the Statistics option to the side menu of Conference Modification.
    """

    zope.interface.implements(INavigationContributor)

    @classmethod
    def fillManagementSideMenu(cls, obj, params={}):
        if obj._conf.canModify(obj._rh._aw):

            if StatisticsRegister().hasActivePlugins():
                params['Statistics'] = wcomponents.SideMenuItem(_('Statistics'),
                    UHConfModifStatistics.getURL(obj._conf))


class StatisticsEFContributor(Component):
    """
    Injects the JSHook objects of all implementations into the event footer.
    """

    zope.interface.implements(IEventDisplayContributor)

    @classmethod
    def eventDetailFooter(cls, obj, vars):
        """
        Add the footer extension for the statistics tracking.
        """
        stats = PluginsHolder().getPluginType('statistics')
        register = StatisticsRegister()

        if not stats.isActive() or not register.hasActivePlugins():
            return False

        key = 'extraFooterContent'
        extension = {}
        tracking = {}

        tracking['trackingActive'] = True
        tracking['trackingHooks'] = register.getAllPluginJSHooks(obj)

        # Build the extension object to be passed to the footer.
        extension['path'] = register.getJSInjectionPath()
        extension['args'] = tracking

        if key not in vars:
            vars[key] = [extension]
        else:
            vars[key].append(extension)


class StatisticsMaterialDownloadListener(Component):
    """
    Provides listener point for implementations to track material downloads.
    """

    zope.interface.implements(IMaterialDownloadListener)

    @classmethod
    def materialDownloaded(cls, obj, resource):
        register = StatisticsRegister()
        listeners = register.getAllPluginDownloadListeners()

        for listener in listeners:
            listener.trackDownload(resource)

        return False


class UHConfModifStatistics(URLHandler):

    _endpoint = 'statistics.view'


class RHStatisticsView(RHConferenceModifBase):

    _register = StatisticsRegister()

    def _checkProtection(self):
        if not PluginsHolder().hasPluginType("statistics"):
            raise PluginError(_("Statistics plugin is not active."))

        self._checkSessionUser()

        RHConferenceModifBase._checkProtection(self)

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self._activeTab = params.pop("tab", 'Piwik')
        self._params = params

    def _process(self):
        return WPStatisticsView(self, WStatisticsView, self._activeTab, self._params).display()


class RHStatisticsHtdocs(RHHtdocs):
    _local_path = pkg_resources.resource_filename(indico.ext.statistics.__name__, "htdocs")


class WStatisticsView(wcomponents.WTemplated):

    def __init__(self, register, activeTab, params):
        self._register = register
        self._confId = params.get('confId')
        self._contribId = params.get('contribId')
        self._startDate = params.get('startDate')
        self._endDate = params.get('endDate')
        self._activeTab = activeTab

    def getVars(self):
        """
        In this method it is expected that any implementations of statistics
        have both a getContributionReport and getConferenceReport method
        defined, the results of which are the data for the view.
        """
        vars = wcomponents.WTemplated.getVars(self)
        plugin = self._register.getPluginByName(self._activeTab, instantiate=False)

        if self._contribId is not None:
            vars["report"] = plugin.getContributionReport(self._startDate, self._endDate,
                                                          self._confId, self._contribId)
        elif self._confId is not None:
            vars["report"] = plugin.getConferenceReport(self._startDate, self._endDate,
                                                        self._confId)
        else:
            raise Exception(_('Cannot instantiate reports view without ID.'))

        return vars


class PluginSettingsContributor(Component):

    zope.interface.implements(IPluginSettingsContributor)

    def hasPluginSettings(self, obj, ptype, plugin):
        return (ptype == 'statistics' and plugin == None)

    def getPluginSettingsHTML(self, obj, ptype, plugin):
        if ptype == 'statistics' and plugin == None:
            return WPluginSettings.forModule(indico.ext.statistics).getHTML()


class WPluginSettings(wcomponents.WTemplated):

    def getVars(self):
        """
        Extend here to add more information to the plugin settings page, hence
        allowing admin only view.
        """
        return wcomponents.WTemplated.getVars(self)


class WPStatisticsView(WPConferenceModifBase):

    def __init__(self, rh, templateClass, activeTab, params):
        WPConferenceModifBase.__init__(self, rh, rh._conf)
        self._rh = rh
        self._conf = self._rh._conf
        self._register = StatisticsRegister()
        self._plugins = self._register.getAllPlugins(activeOnly=True)
        self._templateClass = templateClass
        self._extraJS = []
        self._activeTabName = activeTab
        self._params = params
        self._tabs = []
        self._tabCtrl = wcomponents.TabControl()

    def _addjqPlotPlugins(self, plugins, extraJS):
        """
        Util function to include jqPlot plugins easier.
        """
        if not isinstance(plugins, list):
            plugins = list(plugins)

        prefix = '/statistics/js/lib/jqPlot/plugins/jqplot.'
        suffix = '.min.js'

        for plugin in plugins:
            extraJS.append(prefix + plugin + suffix)

    def _createTabCtrl(self):
        for plugin in self._plugins:
            self._tabs.append(self._tabCtrl.newTab(plugin.getName(),
                plugin.getName(), UHConfModifStatistics.getURL(self._conf,
                                                               tab=plugin.getName())))

    def _getTitle(self):
        return WPConferenceModifBase._getTitle(self) + " - " + _("Statistics")

    def _getPageContent(self, params):
        self._createTabCtrl()
        plugin = self._register.getPluginByName(self._activeTabName)

        if not plugin:
            raise Exception(_('There is no tab called %s available.') % \
                            self._activeTabName)

        return wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(
            self._templateClass.forModule(plugin.getImplementationPackage(),
                                          self._register, self._activeTabName, self._params).getHTML(params))

    def getCSSFiles(self):
        extraCSS = ['/statistics/css/main.css',
                    '/statistics/js/lib/jqTree/jqtree.css',
                    '/statistics/js/lib/jqPlot/jquery.jqplot.css']

        return WPConferenceModifBase.getCSSFiles(self) + extraCSS

    def getJSFiles(self):
        extraJS = ['/statistics/js/statistics.js',
                    '/statistics/js/lib/jqPlot/excanvas.min.js',
                    '/statistics/js/lib/jqTree/tree.jquery.js',
                    '/statistics/js/lib/jqPlot/jquery.jqplot.min.js']

        jqPlotPlugins = ['dateAxisRenderer', 'highlighter', 'cursor']

        self._addjqPlotPlugins(jqPlotPlugins, extraJS)

        return WPConferenceModifBase.getJSFiles(self) + extraJS

    def _setActiveSideMenuItem(self):
        if 'Statistics' in self._pluginsDictMenuItem:
            self._pluginsDictMenuItem['Statistics'].setActive(True)

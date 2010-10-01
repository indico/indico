from MaKaC.webinterface.pages.conferences import WPConferenceModifBase, WPConferenceDefaultDisplayBase
from MaKaC.webinterface import wcomponents, urlHandlers
from MaKaC.webinterface.wcomponents import WTemplated
from MaKaC.common.utils import formatDateTime, parseDateTime
from MaKaC.common.timezoneUtils import getAdjustedDate, nowutc, setAdjustedDate, DisplayTZ, minDatetime
from MaKaC.plugins.base import PluginsHolder
from MaKaC.common.fossilize import fossilize
from MaKaC.plugins.helpers import DBHelpers, PluginFieldsHelper


class WPConfModifChat(WPConferenceModifBase):

    def __init__(self, rh, conf):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._conf = conf
        self._tabs = {} # list of Indico's Tab objects
        self._tabNames = rh._tabs
        self._activeTabName = rh._activeTabName
        self._aw = rh.getAW()

        self._tabCtrl = wcomponents.TabControl()

    #TODO: with wsgi we want to specify another path instead of the usual one for .js files, so we'll have to make some modifications
    #to make possible specifying absoulte paths
    def getJSFiles(self):
        return WPConferenceModifBase.getJSFiles(self) + self._includeJSPackage('Plugins')

    def _createTabCtrl(self):
        for tabName in self._tabNames:
            url = urlHandlers.UHConfModifChat.getURL(self._conf, tab = tabName)
            self._tabs[tabName] = self._tabCtrl.newTab(tabName, tabName, url)

        self._setActiveTab()

    def _setActiveSideMenuItem(self):
        self._pluginsDictMenuItem['Instant Messaging'].setActive(True)

    def _setActiveTab(self):
        self._tabs[self._activeTabName].setActive()

    def _getTitle(self):
        return WPConferenceModifBase._getTitle(self) + " - " + _("Chat management")

    def _getPageContent(self, params):
        if len(self._tabNames) > 0:
            self._createTabCtrl()
            wc = WConfModifChat(self._conf, self._activeTabName, self._tabNames, self._aw)
            return wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(wc.getHTML({}))
        else:
            return _("No available plugins, or no active plugins")


class WPConferenceInstantMessaging(WPConferenceDefaultDisplayBase):

    def __init__(self, rh, conf):
        WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self._conf = conf
        self._aw = rh.getAW()

    def _getBody(self, params):
        wc = WConferenceInstantMessaging(self._conf, self._aw)
        return wc.getHTML({})



class WConfModifChat(wcomponents.WTemplated):

    def __init__(self, conference, activeTab, tabNames, aw):
        self._conf = conference
        self._activeTab = activeTab
        self._tabNames = tabNames
        self._aw = aw
        self._user = aw.getUser()

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["Conference"] = self._conf
        try:
            vars["Chatrooms"] = fossilize( list(DBHelpers.getChatroomList(self._conf)) )
            if len(vars['Chatrooms']) is 0:
                vars['Chatrooms'] = None
        except Exception, e:
            vars["Chatrooms"] = None
        vars['DefaultServer'] = PluginFieldsHelper('InstantMessaging', 'Jabber').getOption('chatServerHost')
        vars["EventDate"] = formatDateTime(getAdjustedDate(nowutc(), self._conf))
        vars["User"] = self._user
        vars["tz"] = DisplayTZ(self._aw,self._conf).getDisplayTZ()

        return vars



class WConferenceInstantMessaging(wcomponents.WTemplated):

    def __init__(self, conference, aw):
        self._conf = conference
        self._aw = aw
        self._user = aw.getUser()

    def getVars( self ):
        vars = WTemplated.getVars( self )

        vars["Conference"] = self._conf
        try:
            vars["Chatrooms"] = DBHelpers.getShowableRooms(self._conf)
        except Exception, e:
            vars["Chatrooms"] = None

        return vars



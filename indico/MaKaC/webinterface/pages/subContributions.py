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
import urllib
from MaKaC.common.TemplateExec import render

import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.materialFactories as materialFactories
import MaKaC.webinterface.navigation as navigation
import MaKaC.webinterface.linking as linking
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.webinterface.common.person_titles import TitlesRegistry
from xml.sax.saxutils import quoteattr
from MaKaC.webinterface.pages.conferences import WPConferenceDefaultDisplayBase, WPConferenceBase, WPConferenceModifBase
from indico.core.config import Config
from datetime import datetime
from MaKaC.common.utils import isStringHTML
from MaKaC.i18n import _
from indico.util.i18n import i18nformat
from MaKaC.common.fossilize import fossilize
from MaKaC.fossils.subcontribution import ISubContribParticipationFullFossil


class WPSubContributionBase( WPMainBase, WPConferenceBase ):

    def __init__( self, rh, subContribution ):
        self._subContrib = self._target = subContribution
        self._conf = self._target.getConference()
        self._contrib = self._subContrib.getOwner()
        WPConferenceBase.__init__( self, rh, self._conf )


class WPSubContributionDefaultDisplayBase(WPConferenceDefaultDisplayBase, WPSubContributionBase):
    def __init__(self, rh, contribution):
        WPSubContributionBase.__init__(self, rh, contribution)

    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self) + \
               self._includeJSPackage('Management') + \
               self._includeJSPackage('MaterialEditor') + \
               self._asset_env['contributions_js'].urls()

    def getCSSFiles(self):
        return WPConferenceDefaultDisplayBase.getCSSFiles(self) + \
               self._asset_env['contributions_sass'].urls()

    def _getHeadContent(self):
        return WPConferenceDefaultDisplayBase._getHeadContent(self) + render('js/mathjax.config.js.tpl') + \
               '\n'.join(['<script src="{0}" type="text/javascript"></script>'.format(url)
                          for url in self._asset_env['mathjax_js'].urls()])


class WSubContributionDisplayBase(wcomponents.WTemplated):
    def __init__(self, aw, subContrib):
        self._aw = aw
        self._subContrib = subContrib

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["duration"] =(datetime(1900,1,1)+self._subContrib.getDuration()).strftime("%H:%M")
        vars["SubContrib"] = self._subContrib
        vars["accessWrapper"] = self._aw
        vars["reportNumberSystems"] = Config.getInstance().getReportNumberSystems()

        return vars

class WSubContributionDisplayFull(WSubContributionDisplayBase):
    pass

class WSubContributionDisplayMin(WSubContributionDisplayBase):
    pass

class WSubContributionDisplay:
    def __init__(self, aw, subContrib):
        self._aw=aw
        self._subContrib=subContrib

    def getHTML(self, params={}):
        if self._subContrib.canAccess( self._aw ):
            c = WSubContributionDisplayFull( self._aw, self._subContrib)
            return c.getHTML( params )
        if self._subContrib.canView( self._aw ):
            c = WSubContributionDisplayMin( self._aw, self._subContrib)
            return c.getHTML( params )
        return ""

class WPSubContributionDisplay(WPSubContributionDefaultDisplayBase):
    navigationEntry=navigation.NESubContributionDisplay

    def _getBody(self, params):
        wc=WSubContributionDisplay(self._getAW(),self._subContrib)
        return wc.getHTML()

class WPSubContributionModifBase( WPConferenceModifBase ):

    def __init__( self, rh, subContribution ):
        WPConferenceModifBase.__init__( self, rh, subContribution.getConference() )
        self._subContrib = self._target = subContribution
        self._conf = self._target.getConference()
        self._contrib = self._subContrib.getOwner()

    def getJSFiles(self):
        return WPConferenceModifBase.getJSFiles(self) + \
               self._asset_env['contributions_js'].urls()

    def getCSSFiles(self):
        return WPConferenceModifBase.getCSSFiles(self) + \
               self._asset_env['contributions_sass'].urls()

    def _getHeadContent(self):
        return WPConferenceModifBase._getHeadContent(self) + render('js/mathjax.config.js.tpl') + \
               '\n'.join(['<script src="{0}" type="text/javascript"></script>'.format(url)
                          for url in self._asset_env['mathjax_js'].urls()])

    def _getNavigationDrawer(self):
        pars = {"target": self._subContrib, "isModif": True}
        return wcomponents.WNavigationDrawer( pars, bgColor="white" )

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main", _("Main"), \
                urlHandlers.UHSubContributionModification.getURL( self._target ) )
        #self._tabMaterials = self._tabCtrl.newTab( "materials", _("Files"), \
        self._tabMaterials = self._tabCtrl.newTab( "materials", _("Material"), \
                urlHandlers.UHSubContribModifMaterials.getURL( self._target ) )
        self._tabTools = self._tabCtrl.newTab( "tools", _("Tools"), \
                urlHandlers.UHSubContribModifTools.getURL( self._target ) )
        self._setActiveTab()

    def _getPageContent( self, params ):
        self._createTabCtrl()

        banner = wcomponents.WTimetableBannerModif(self._getAW(), self._target).getHTML()
        body = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )

        return banner + body

    def _setActiveSideMenuItem(self):
        if self._contrib.isScheduled():
            self._timetableMenuItem.setActive(True)
        else:
            self._contribListMenuItem.setActive(True)

    def _getTabContent( self, params ):
        return "nothing"


class WPSubContribModifMain( WPSubContributionModifBase ):

    def _setActiveTab( self ):
        self._tabMain.setActive()


class WSubContribModifTool(wcomponents.WTemplated):
    pass


class WPSubContributionModifTools( WPSubContributionModifBase ):

    def _setActiveTab( self ):
        self._tabTools.setActive()

    def _getTabContent( self, params ):
        return WSubContribModifTool().getHTML({"deleteSubContributionURL": urlHandlers.UHSubContributionDelete.getURL( self._target )})


class WPSubContributionModifMaterials( WPSubContributionModifBase ):
    #TODO: maybe join it with contributions.WPContributionModifMaterials

    _userData = ['favorite-user-list']

    def __init__(self, rh, subcontribution):
        WPSubContributionModifBase.__init__(self, rh, subcontribution)

    def _setActiveTab( self ):
        self._tabMaterials.setActive()

    def _getTabContent( self, pars ):
        wc=wcomponents.WShowExistingMaterial(self._target)
        #pars["materialTypes"] = self._matTypes
        return wc.getHTML()


class WPSubContributionModification( WPSubContribModifMain ):
    def _getTabContent( self, params ):
        wc = WSubContribModifMain( self._target, materialFactories.ContribMFRegistry() )
        place = ""
        if self._target.getLocation() is not None:
            place = self._target.getLocation().getName()
        pars = { "dataModificationURL": urlHandlers.UHSubContributionDataModification.getURL( self._target ), \
                "categDisplayURLGen": urlHandlers.UHCategoryDisplay.getURL, \
                "deleteSubContribURL": urlHandlers.UHSubContributionDelete.getURL, \
                "place": place, \
                "duration": (datetime(1900,1,1)+self._target.getDuration()).strftime("%Hh%M'"), \
                "confId": self._target.getConference().getId(), \
                "contribId": self._target.getOwner().getId(), \
                "subContribId": self._target.getId()}
        return wc.getHTML( pars )

class WSubContributionDataModification(wcomponents.WTemplated):

    def __init__( self, subContribution ):
        self.__subContrib = subContribution
        self.__owner = self.__subContrib.getOwner()

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["title"] = self.__subContrib.getTitle()
        vars["description"] = self.__subContrib.getDescription()
        vars["keywords"] = self.__subContrib.getKeywords()
        vars["durationHours"] = (datetime(1900,1,1)+self.__subContrib.getDuration()).hour
        vars["durationMinutes"] = (datetime(1900,1,1)+self.__subContrib.getDuration()).minute
        vars["locator"] = self.__subContrib.getLocator().getWebForm()
        vars["speakers"] = self.__subContrib.getSpeakerText()
        return vars


class WPSubContribData( WPSubContribModifMain ):

    def _getTabContent( self, params ):
        wc = WSubContributionDataModification(self._target)
        params["postURL"] = urlHandlers.UHSubContributionDataModif.getURL(self._subContrib)
        return wc.getHTML( params )


class WSubContributionDeletion(object):

    def __init__( self, subContribList ):
        self._subContribList = subContribList

    def getHTML( self, actionURL ):
        subcontribs = ''.join(list("<li>{0}</li>".format(s.getTitle()) for s in self._subContribList))

        msg = {'challenge': _("Are you sure that you want to delete the following subcontributions?"),
               'target': "<ul>{0}</ul>".format(subcontribs)
               }

        wc = wcomponents.WConfirmation()

        subContribIdList = list(sc.getId() for sc in self._subContribList)

        return wc.getHTML(msg, actionURL, {"selectedCateg": subContribIdList},
                          confirmButtonCaption= _("Yes"),
                          cancelButtonCaption= _("No") )


class WPSubContributionDeletion( WPSubContributionModifTools ):

    def _getTabContent( self, params ):
        wc = WSubContributionDeletion( [self._target] )
        return wc.getHTML( urlHandlers.UHSubContributionDelete.getURL( self._target ) )

class WPSubContributionModificationClosed( WPSubContribModifMain ):

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main", _("Main"), "")

    def _getTabContent( self, params ):
        if self._subContrib.getOwner().getSession() != None:
            message = _("The session is currently locked and you cannot modify it in this status. ")
            if self._subContrib.getOwner().getConference().canModify(self._rh.getAW()):
                message += _("If you unlock the session, you will be able to modify its details again.")
            url = urlHandlers.UHSessionOpen.getURL(self._subContrib.getOwner().getSession())
            unlockButtonCaption = _("Unlock session")
        else:
            message = _("The event is currently locked and you cannot modify it in this status. ")
            if self._subContrib.getOwner().getConference().canModify(self._rh.getAW()):
                message += _("If you unlock the event, you will be able to modify its details again.")
            url = urlHandlers.UHConferenceOpen.getURL(self._subContrib.getOwner().getConference())
            unlockButtonCaption = _("Unlock event")
        return wcomponents.WClosed().getHTML({"message": message,
                                             "postURL":url,
                                             "showUnlockButton": self._subContrib.getOwner().getConference().canModify(self._rh.getAW()),
                                             "unlockButtonCaption": unlockButtonCaption})

class WSubContribModifMain(wcomponents.WTemplated):

    def __init__( self, subContribution, mfRegistry ):
        self._subContrib = subContribution
        self._mfRegistry = mfRegistry

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["locator"] = self._subContrib.getLocator().getWebForm()
        vars["title"] = self._subContrib.getTitle()
        if isStringHTML(self._subContrib.getDescription()):
            vars["description"] = self._subContrib.getDescription()
        else:
            vars["description"] = """<table class="tablepre"><tr><td><pre>%s</pre></td></tr></table>""" % self._subContrib.getDescription()
        vars["dataModifButton"] = ""
        vars["dataModifButton"] =  _("""<input type="submit" class="btn" value="_("modify")">""")
        vars["reportNumbersTable"]=wcomponents.WReportNumbersTable(self._subContrib,"subcontribution").getHTML()
        vars["keywords"] = self._subContrib.getKeywords()
        vars["confId"] = self._subContrib.getConference().getId()
        vars["contribId"] = self._subContrib.getContribution().getId()
        vars["subContribId"] = self._subContrib.getId()
        vars["presenters"] = fossilize(self._subContrib.getSpeakerList(), ISubContribParticipationFullFossil)
        vars["authors"] = fossilize(self._subContrib.getContribution().getAllAuthors())
        vars["eventType"] = self._subContrib.getConference().getType()
        return vars



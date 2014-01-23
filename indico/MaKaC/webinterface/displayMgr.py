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

from indico.core.db import DBMgr
from BTrees import OOBTree
from persistent import Persistent
from MaKaC.common.Counter import Counter
from MaKaC.common.Locators import Locator
from MaKaC.webinterface import urlHandlers
from MaKaC.trashCan import TrashCanManager
import MaKaC.webinterface.internalPagesMgr as internalPagesMgr
from MaKaC.errors import MaKaCError
from MaKaC.conference import LocalFile
from MaKaC.plugins.base import Observable
import re
from indico.util.contextManager import ContextManager
from indico.util.i18n import _, N_


class ConfDisplayMgrRegistery:
    """
    Class to get the DisplayMgr for a conference
    """

    def __init__(self):
        self._displayMgrRegistery = None

    def _getDisplayMgrRegistery( self ):
        #DBMgr.getInstance().commit()
        if not self._displayMgrRegistery:
            db_root = DBMgr.getInstance().getDBConnection().root()
            if db_root.has_key( "displayRegistery" ):
                self._displayMgrRegistery = db_root["displayRegistery"]
            else:
                self._displayMgrRegistery = OOBTree.OOBTree()
                db_root["displayRegistery"] = self._displayMgrRegistery
        return self._displayMgrRegistery


    def registerDisplayMgr( self, conference, dispMgr ):
        """Associates a given conference with a confDispplayMgr
        """
        self._getDisplayMgrRegistery()[ conference.getId() ] = dispMgr

    def getDisplayMgr( self, conference, update=False ):
        """Gives back the webfactory associated with a given conference or None
            if no association exists
        """
        if self._getDisplayMgrRegistery().has_key( conference.getId() ):
            DM = self._getDisplayMgrRegistery()[ conference.getId() ]
            # as the object can just coming out the database, we must update the system link of the menu
            if update:
                DM.getMenu().updateSystemLink()
            return DM
        DM = ConfDisplayMgr(conference, Menu(conference))
        self.registerDisplayMgr(conference, DM)
        # as the object just coming out the database, we must update the system link of the menu
        DM.getMenu().updateSystemLink()
        return DM


class DisplayMgr(Persistent):
    """
    base class for the DisplayMgr object
    """

    def __init__(self):
        pass

class ConfDisplayMgr(DisplayMgr):
    """
    DisplayMgr for a conference
    """

    def __init__(self, conf, menu=None, format=None, tickerTape=None):
        self._conf = conf
        if menu:
            self._menu = menu
        else:
            self._menu = Menu(self._conf, self)
        if format:
            self._format = format
        else:
            self._format = Format()
        if tickerTape:
            self._tickerTape = tickerTape
        else:
            self._tickerTape = TickerTape()
        self._defaultstyle = ""
        #################################
        # Fermi timezone awareness      #
        #################################
        self.defaulttimezone = ""
        #################################
        # Fermi timezone awareness(end) #
        #################################

        # Search is enabled, by default
        self._searchEnabled = True

        #Manager for all the images stored in the conference
        self._imagesMngr = ImagesManager(conf)

        #Manager for CSS file rendering the main display page for the conference
        self._styleMngr = StyleManager(conf)

        # Displaying navigation bar
        self._displayNavigationBar = True

        self._showSocialApps = True

    def clone(self, conf):
        newCdm = ConfDisplayMgrRegistery().getDisplayMgr(conf, update=False)
        # default style
        newCdm.setDefaultStyle(self.getDefaultStyle())
        # clone the menu
        self.getMenu().clone(newCdm)
        # clone the format
        self.getFormat().clone(newCdm)
        # clone the tickertape
        self.getTickerTape().clone(newCdm)
        # clone the imagesmanager
        self.getImagesManager().clone(newCdm)
        # clone the imagesmanager
        self.getStyleManager().clone(newCdm)
        return newCdm

    def getDefaultStyle( self ):
        """Returns the default view of the conference"""
        try:
            return self._defaultstyle
        except:
            self._defaultstyle = ""
            return self._defaultstyle

    def setDefaultStyle( self, style ):
        self._defaultstyle = style

    #################################
    # Fermi timezone awareness      #
    #################################
    def getDefaultTimezone(self):
        try:
            return self._defaulttimezone
        except:
            self._defaulttimezone = ""
            return self._defaulttimezone

    def setDefaultTimezone(self, tz):
        self._defaulttimezone = tz

    #################################
    # Fermi timezone awareness(end) #
    #################################

    def getShowSocialApps(self):
        if not hasattr(self, '_showSocialApps'):
            self._showSocialApps = True
        return self._showSocialApps

    def setShowSocialApps(self, value):
        self._showSocialApps = value

    def getDisplayNavigationBar(self):
        if not hasattr(self, "_displayNavigationBar"):
            self._displayNavigationBar = True
        return self._displayNavigationBar

    def setDisplayNavigationBar(self, value):
        self._displayNavigationBar = value

    def getMenu(self):
        if self._menu.getParent() == None:
            self._menu.setParent(self)
        return self._menu

    def getConference(self):
        return self._conf

    def getFormat(self):
        try:
            if self._format:
                pass
        except AttributeError, e:
            self._format = Format()
        return self._format

    def getSearchEnabled(self):
        if ContextManager.get('offlineMode', False):
            return False
        try:
            return self._searchEnabled
        except AttributeError:
            self._searchEnabled = True
        return self._searchEnabled

    def setSearchEnabled(self, value):
        self._searchEnabled = value

    def getTickerTape(self):
        try:
            if self._tickerTape:
                pass
        except AttributeError, e:
            self._tickerTape = TickerTape()
        return self._tickerTape

    def getImagesManager(self):
        try:
            if self._imagesMngr:
                pass
        except AttributeError, e:
            self._imagesMngr = ImagesManager(self._conf)
        return self._imagesMngr

    def getStyleManager(self):
        try:
            if self._styleMngr:
                pass
        except AttributeError, e:
            self._styleMngr = StyleManager(self._conf)
        return self._styleMngr

class Menu(Persistent):
    """
    class to configure a menu
    """

    def __init__(self, conf, parent=None):
        self._listLink = []
        self._parent = parent
        self._conf = conf
        self._indent = "&nbsp;&nbsp;&nbsp;&nbsp;"
        self._linkGenerator = Counter()
        self._timetable_detailed_view = False
        self._timetable_layout = 'normal'

    def clone(self, cdm):
        newMenu = cdm.getMenu()
        newMenu.set_timetable_detailed_view(self.is_timetable_detailed_view())
        newMenu.set_timetable_layout(self.get_timetable_layout())
        newMenu._linkGenerator = self._linkGenerator.clone()
        newList = []
        for link in self.getLinkList():
            newList.append(link.clone(newMenu))
        if len(newList) != 0:
            newMenu._listLink = newList

        # change system links to new event id
        newMenu.updateSystemLink()

        return newMenu

    def enable(self):
        pass

    def disable(self):
        pass

    def getName(self):
        return ""

    def getConference(self):
        return self._conf

    def updateSystemLink(self):
        systemLinkData = SystemLinkData(self._conf)
        linksData = systemLinkData.getLinkData()
        linksDataOrderedKeys = systemLinkData.getLinkDataOrderedKeys()

        #remove system links (and sublinks) which are not define in linksData
        for link in self.getAllLinks()[:]:
            if isinstance(link, SystemLink):
                if link.getParent() is not None:
                    if not link.getName() in linksData:
                        link.getParent().removeLink(link)
                    elif link.getParent().getName() != linksData[link.getName()]["parent"]:
                        link.getParent().removeLink(link)
                elif link.getName() not in linksData:
                    # link was removed from the list
                    self.removeLink(link)

        #Now, update the system links
        for name in linksDataOrderedKeys:
            data = linksData[name]
            link = self.getLinkByName(name)
            if link:
                # only update the caption if it has been already customized
                if not link.wasChanged() or link.getCaption() == '':
                    link.setCaption(data["caption"], silent=True)
                link.setURLHandler(data["URL"])
                link.setDisplayTarget(data.get("displayTarget",""))
            else:
                #we must create the link
                self._createSystemLink(name, linksData)

    def _createSystemLink(self, name, linksData):
        data = linksData.get(name, None)
        if data == None:
            raise MaKaCError(_("error in the system link structure of the menu"))
        if data["parent"] == "":
            #create the link at the fisrt level
            link = SystemLink(name)
            link.setCaption(data["caption"], silent=True)
            link.setURLHandler(data["URL"])
            self.addLink(link)
            link.disable()
            if data.get("visibilityByDefault", True):
                link.enable()
        else:
            #We must check if the parent exist
            parent = self.getLinkByName(data["parent"])
            if not parent:
                self._createSystemLink(data["parent"], linksData)
                parent = self.getLinkByName(data["parent"])
            #We can create the link under the parent
            link = SystemLink(name)
            link.setCaption(data["caption"], silent=True)
            link.setURLHandler(data["URL"])
            parent.addLink(link)
            link.disable()
            if data.get("visibilityByDefault", True):
                link.enable()

    def _generateNewLinkId( self ):
        """Returns a new unique identifier for the current conference
            contributions
        """
        return str(self._linkGenerator.newCount())

    def linkHasToBeDisplayed(self, link):
        if isinstance(link, SystemLink):
            if link.getName()=="CFA" or link.getName()=="abstractsBook" or link.getName()=="mytracks" or link.getName()=="manageTrack":
                return self.getConference().hasEnabledSection("cfa")
            elif link.getName()=="registrationForm" or link.getName()=="registrants":
                return self.getConference().hasEnabledSection("regForm")
            else:
                return True
        else:
            return True

    def getLocator( self ):
        """Gives back a globaly unique identification encapsulated in a Locator
            object for the session instance
        """
        if self._parent == None:
            return Locator()
        lconf = self._parent.getConference().getLocator()
        return lconf

    def setParent(self, parent):
        self._parent = parent

    def getParent(self):
        return self._parent

    def getIndent(self):
        return self._indent

    def setIndent(self, indent):
        self._indent = indent

    def addLink(self, link):
        self._listLink.append(link)
        link.setParent(self)
        id = link.getId()
        if id == "":
            id = self._generateNewLinkId()
        link.setId(id)
        self._p_changed = 1

    def removeLink(self, link):
        if link in self._listLink:
            self._listLink.remove(link)
            link.setParent(None)
            link.delete()
            self._p_changed = 1

    def upLink(self, link):
        if link in self._listLink:
            index = self._listLink.index(link)
            newindex = index - 1
            while newindex >= 0 and not self.linkHasToBeDisplayed(self._listLink[newindex]):
                newindex -= 1
            self._listLink.remove(link)
            if newindex >= 0:
                self._listLink.insert(newindex, link)
            else:
                self._listLink.append(link)
            self._p_changed = 1


    def downLink(self, link):
        if link in self._listLink:
            index = self._listLink.index(link)
            newindex = index+1
            while newindex < len(self._listLink) and not self.linkHasToBeDisplayed(self._listLink[newindex]):
                newindex += 1
            self._listLink.remove(link)
            if newindex <= len(self._listLink):
                self._listLink.insert(newindex, link)
            else:
                self._listLink.insert(0, link)
            self._p_changed = 1

    def getLinkById(self, id):
        for link in self._listLink:
            if link.getId() == id:
                return link
            ret = link.getLinkById(id)
            if ret:
                return ret
        return None

    def getLinkByName(self, name):
        for link in self._listLink:
            if link.getName() == name:
                return link
            ret = link.getLinkByName(name)
            if ret:
                return ret
        return None

    def getAllLinks(self):
        l = []
        for link in self._listLink:
            if isinstance(link,Spacer):
                continue
            l.append(link)
            l.extend(link._listLink)
        return l

    def getLinkList(self):
        return self._listLink

    def getEnabledLinkList(self):
        l = []
        for link in self._listLink:
            if link.isEnabled():
                l.append(link)
        return l

    def isCurrentItem(self, item):
        return self.getCurrentItem() == item

    def setCurrentItem(self, value):
        self._v_currentItem = value

    def getCurrentItem(self):
        return getattr(self, '_v_currentItem', None)

    def set_timetable_layout(self, layout):
        self._timetable_layout = layout

    def toggle_timetable_layout(self):
        if self._timetable_layout == 'normal':
            self.set_timetable_layout('room')
        else:
            self.set_timetable_layout('normal')

    def get_timetable_layout(self):
        try:
            return self._timetable_layout
        except AttributeError:
            self._timetable_layout = 'normal'
            return self._timetable_layout

    def set_timetable_detailed_view(self, view):
        self._timetable_detailed_view = view

    def is_timetable_detailed_view(self):
        try:
            return self._timetable_detailed_view
        except AttributeError:
            self._timetable_detailed_view = False
            return self._timetable_detailed_view

    def __str__(self):
        str = ""
        for link in self._listLink:
            if link.isEnabled():
                str += "%s\n" % link
        return str


class Spacer(Persistent):
    Type = "spacer"

    def __init__(self, name="", parent=None):
        self._name = name
        self._active = True
        self._parent = parent
        self._id = ""
        self._v_visible=True

    def clone(self, newMenu):
        newSpacer = Spacer(name=self.getName(),parent=newMenu)
        newSpacer.setId(self.getId())
        newSpacer.setEnabled(self.isEnabled())
        return newSpacer

    def getParent(self):
        return self._parent

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id
        if self._name == "":
            self._name = "spacer %s"%id

    def getLocator( self ):
        """Gives back a globaly unique identification encapsulated in a Locator
            object for the session instance
        """
        if self._parent == None:
            return Locator()
        lparent = self._parent.getLocator()
        lparent["linkId"] = self.getId()
        return lparent

    def getLinkById(self, id):
        return None

    def getLinkByName(self, name):
        return None

    def setParent(self, parent):
        self._parent = parent

    def getType(self):
        return self.Type

    def enable(self):
        self._active = True

    def disable(self):
        self._active = False

    def setEnabled(self, value):
        if value:
            self.enable()
        else:
            self.disable()

    def isEnabled(self):
        return self._active

    def setName(self, name):
        self._name = name

    def getName(self):
        return self._name

    def __str__(self, indent=""):
        str = """%s<br>\n"""%indent
        return str

    def isVisible(self):
        try:
            if self._v_visible:
                pass
        except AttributeError:
            self._v_visible=True
        return self._v_visible

    def setVisible(self,newValue=True):
        self._v_visible=newValue

    def delete(self):
        TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)


class Link(Persistent):
    """
    base class for the links of a menu
    """
    Type = "Link"

    def __init__(self, name, parent=None):
        self._name = name
        self._listLink = []
        self._active = True
        self._parent = parent
        self._id = ""
        self._caption = ""
        self._v_visible=True
        self._displayTarget = ""

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id

    def getParent(self):
        return self._parent

    def getLocator( self ):
        """Gives back a globaly unique identification encapsulated in a Locator
            object for the session instance
        """
        if self._parent == None:
            return Locator()
        lparent = self._parent.getLocator()
        lparent["linkId"] = self.getId()
        return lparent

    def _generateNewLinkId( self ):
        """Returns a new unique identifier for the current conference
            contributions
        """
        if self._parent:
            return self._parent._generateNewLinkId()

    def setParent(self, parent):
        self._parent = parent

    def getType(self):
        return self.Type

    def getDisplayTarget(self):
        try:
            if self._displayTarget:
                pass
        except AttributeError, e:
            self._displayTarget = "_blank"
        return self._displayTarget

    def setDisplayTarget(self, t):
        self._displayTarget = t

    def enable(self):
        previousState = self._active
        self._active = True
        if not previousState:
            for link in self._listLink:
                link.enable()
            self._p_changed = 1
        self._parent.enable()

    def disable(self):
        self._active = False
        for link in self._listLink:
            link.disable()
        self._p_changed = 1

    def setEnabled(self, enable):
        if enable:
            self.enable()
        else:
            self.disable()

    def isEnabled(self):
        return self._active

    def setName(self, name):
        self._name = name

    def getName(self):
        return self._name

    def setCaption(self, caption):
        self._caption = caption

    def getCaption(self):
        return self._caption

    def addLink(self, link):
        self._listLink.append(link)
        link.setParent(self)
        id = link.getId()
        if id == "":
            id = self._generateNewLinkId()
        link.setId(id)
        self._p_changed = 1

    def removeLink(self, link):
        if link in self._listLink:
            self._listLink.remove(link)
            link.setParent(None)
            link.delete()
            self._p_changed = 1

    def upLink(self, link):
        if link in self._listLink:
            if self._listLink.index(link) != 0:
                index = self._listLink.index(link)
                sb = self._listLink.pop(index)
                self._listLink.insert(index-1, sb)
                self._p_changed = 1

    def downLink(self, link):
        if link in self._listLink:
            if self._listLink.index(link) < len(self._listLink)-1:
                index = self._listLink.index(link)
                sb = self._listLink.pop(index)
                self._listLink.insert(index+1, sb)
                self._p_changed = 1

    def getLinkByName(self, name):
        for link in self._listLink:
            if link.getName() == name:
                return link
            ret = link.getLinkByName(name)
            if ret:
                return ret
        return None

    def getLinkById(self, id):
        for link in self._listLink:
            if link.getId() == id:
                return link
            ret = link.getLinkById(id)
            if ret:
                return ret
        return None

    def getLinkList(self):
        return self._listLink

    def getEnabledLinkList(self):
        l = []
        for link in self._listLink:
            if link.isEnabled():
                l.append(link)
        return l

    def getURL(self):
        return ""

    def __str__(self, indent=""):
        str = """%s<a href="%s">%s</a><br>\n"""%(indent, self.getURL(), self.getName())
        for link in self._listLink:
            if link.isEnabled():
                str += "%s\n"%link.__str__(indent + "&nbsp;&nbsp;&nbsp;&nbsp;")
        return str

    def isVisible(self):
        try:
            if self._v_visible:
                pass
        except AttributeError:
            self._v_visible=True
        return self._v_visible

    def setVisible(self,newValue=True):
        self._v_visible=newValue

    def delete(self):
        for l in self.getLinkList()[:]:
            self.removeLink(l)
        TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)

    def getMenu(self):
        """
        Go up till the "parent menu" is found
        """
        if isinstance(self._parent, Menu):
            return self._parent
        else:
            return self._parent.getMenu()

class SystemLink(Link):
    """
    class for link which target a system part
    The user cannot change the link data
    The URL is dynamicly generated
    """
    Type = "system"

    def __init__(self, name, parent=None, changed=False):
        Link.__init__(self, name, parent)

        # by default, this link will be updated when there are version
        # changes that modify its default name
        self._changed = changed

    def clone(self, newMenu):
        newLink = SystemLink(self.getName(), parent=newMenu, changed=self.wasChanged())
        newLink.setEnabled(self.isEnabled())
        newLink.setVisible(self.isVisible())
        newLink.setId(self.getId())
        newLink.setDisplayTarget(self.getDisplayTarget())
        newLink.setCaption(self.getCaption(), silent=True)
        newLink.setURLHandler(self.getURLHandler())

        listLink = []
        for link in self.getLinkList():
            listLink.append(link.clone(newLink))

        newLink._listLink = listLink

        return newLink

    def wasChanged(self):
        # old conferences, before `_changed` was introduced
        if hasattr(self, '_changed'):
            return self._changed
        else:
            # for old conferences, just keeps things as people
            # left them
            return True

    def _getURLObject(self):
        # TOREMOVE: fix events with "absolute" URL
        if not hasattr(self, '_URLHandler'):
            self.getMenu().updateSystemLink()
        if isinstance(self._URLHandler, str):
            if self._URLHandler.startswith("http"):  # Fix for hardcoded URLs
                self.getMenu().updateSystemLink()
            handler = getattr(urlHandlers, self._URLHandler)
        else:
            handler = self._URLHandler
        return handler.getURL(self.getMenu().getConference())

    def getURL(self):
        url = str(self._getURLObject())
        if self._name == 'timetable':
            menu = self.getMenu()
            if menu.get_timetable_layout() == 'room':
                url += '?ttLyt=room'
            if menu.is_timetable_detailed_view():
                startDate = menu.getConference().getSchedule().getAdjustedStartDate()
                url += startDate.strftime('#%Y%m%d')
                url += '.detailed'
        return url

    def getURLHandler(self):
        if not hasattr(self, '_URLHandler'):
            self.getMenu().updateSystemLink()
        return self._URLHandler

    def setURLHandler(self, url):
        self._URLHandler = url

    def getCaption(self):
        return self._caption

    def setCaption(self, caption, silent=False):
        self._caption = caption

        if not silent:
            # if the caption was changed, do not update it when the default
            # value get an update
            self._changed = True

    def isVisible(self):
        return self._getURLObject().valid and super(SystemLink, self).isVisible()

class SystemLinkData(Observable):

    def __init__(self, conf=None):
        #the following dict is used to update the system link of the menu. each new entry is added to the menu,
        #and all entries in the menu whiche are not is this dict are removed.
        if not hasattr(self, "_linkData"):
            self._linkData = {
                "overview": {
                    "caption": N_("Overview"),
                    "URL": 'UHConferenceOverview',
                    "parent": ""},
                "programme": {
                    "caption": N_("Scientific Programme"),
                    "URL": 'UHConferenceProgram',
                    "parent": ""},
                "CFA": {
                    "caption": N_("Call for Abstracts"),
                    "URL": 'UHConferenceCFA',
                    "parent": ""},
                "ViewAbstracts": {
                    "caption": N_("View my Abstracts"),
                    "URL": 'UHUserAbstracts',
                    "parent": "CFA"},
                "SubmitAbstract": {
                    "caption": N_("Submit Abstract"),
                    "URL": 'UHAbstractSubmission',
                    "parent": "CFA"},
                "manageTrack": {
                    "caption": N_("Manage my Tracks"),
                    "URL": 'UHConfMyStuffMyTracks',
                    "parent": "programme"},
                "timetable": {
                    "caption": N_("Timetable"),
                    "URL": 'UHConferenceTimeTable',
                    "parent": ""},
                "contributionList": {
                    "caption": N_("Contribution List"),
                    "URL": 'UHContributionList',
                    "parent": ""},
                "authorIndex": {
                    "caption": N_("Author List"),
                    "URL": 'UHConfAuthorIndex',
                    "parent": ""},
                "speakerIndex": {
                    "caption": N_("Speaker List"),
                    "URL": 'UHConfSpeakerIndex',
                    "parent": "",
                    "visibilityByDefault": False},
                "mystuff": {
                    "caption": N_("My Conference"),
                    "URL": 'UHConfMyStuff',
                    "parent": ""},
                "mytracks": {
                    "caption": N_("My Tracks"),
                    "URL": 'UHConfMyStuffMyTracks',
                    "parent": "mystuff"},
                "mysessions": {
                    "caption": N_("My Sessions"),
                    "URL": 'UHConfMyStuffMySessions',
                    "parent": "mystuff"},
                "mycontribs": {
                    "caption": N_("My Contributions"),
                    "URL": 'UHConfMyStuffMyContributions',
                    "parent": "mystuff"},
                "paperreviewing": {
                    "caption": N_("Paper Reviewing"),
                    "URL": 'UHPaperReviewingDisplay',
                    "parent": ""},
                "managepaperreviewing": {
                    "caption": N_("Manage Paper Reviewing"),
                    "URL": 'UHConfModifReviewingPaperSetup',
                    "parent": "paperreviewing"},
                "assigncontributions": {
                    "caption": N_("Assign Papers"),
                    "URL": 'UHConfModifReviewingAssignContributionsList',
                    "parent": "paperreviewing"},
                "judgelist": {
                    "caption": N_("Referee Area"),
                    "URL": 'UHConfModifListContribToJudge',
                    "parent": "paperreviewing"},
                "judgelistreviewer": {
                    "caption": N_("Content Reviewer Area"),
                    "URL": 'UHConfModifListContribToJudgeAsReviewer',
                    "parent": "paperreviewing"},
                "judgelisteditor": {
                    "caption": N_("Layout Reviewer Area"),
                    "URL": 'UHConfModifListContribToJudgeAsEditor',
                    "parent": "paperreviewing"},
                "uploadpaper": {
                    "caption": N_("Upload Paper"),
                    "URL": 'UHUploadPaper',
                    "parent": "paperreviewing"},
                "downloadtemplate": {
                    "caption": N_("Download Template"),
                    "URL": 'UHDownloadPRTemplate',
                    "parent": "paperreviewing"},
                "abstractsBook": {
                    "caption": N_("Book of Abstracts"),
                    "URL": 'UHConfAbstractBook',
                    "parent": "",
                    "displayTarget": "_blank"},
                "registrationForm": {
                    "caption": N_("Registration"),
                    "URL": 'UHConfRegistrationForm',
                    "parent": ""},
                "ViewMyRegistration": {
                    "caption": N_("Modify my Registration"),
                    "URL": 'UHConfRegistrationFormModify',
                    "parent": "registrationForm"},
                "downloadETicket": {
                    "caption": N_("Download e-ticket"),
                    "URL": 'UHConferenceTicketPDF',
                    "parent": "registrationForm"},
                "NewRegistration": {
                    "caption": N_("Registration Form"),
                    "URL": 'UHConfRegistrationFormDisplay',
                    "parent": "registrationForm"},
                "registrants": {
                    "caption": N_("Participant List"),
                    "URL": 'UHConfRegistrantsList',
                    "parent": "",
                    "visibilityByDefault": False},
                "evaluation": {
                    "caption": N_("Evaluation"),
                    "URL": 'UHConfEvaluationMainInformation',
                    "parent": ""},
                "newEvaluation": {
                    "caption": N_("Evaluation Form"),
                    "URL": 'UHConfEvaluationDisplay',
                    "parent": "evaluation"},
                "viewMyEvaluation": {
                    "caption": N_("Modify my Evaluation"),
                    "URL": 'UHConfEvaluationDisplayModif',
                    "parent": "evaluation"}
            }
            self._notify('confDisplaySMFillDict', {'dict': self._linkData, 'conf': conf})

        #this ordered list allow us to keep the order we want for the menu
        if not hasattr(self, "_linkDataOrderedKeys"):
            self._linkDataOrderedKeys = ["overview",
                                        "programme",
                                        "CFA",
                                        "ViewAbstracts",
                                        "SubmitAbstract",
                                        "manageTrack",
                                        "timetable",
                                        "contributionList",
                                        "authorIndex",
                                        "speakerIndex",
                                        "mystuff",
                                        "mytracks",
                                        "mysessions",
                                        "mycontribs",
                                        "paperreviewing",
                                        "managepaperreviewing",
                                        "assigncontributions",
                                        "judgelist",
                                        "judgelistreviewer",
                                        "judgelisteditor",
                                        "uploadpaper",
                                        "downloadtemplate",
                                        "abstractsBook",
                                        "registrationForm",
                                        "ViewMyRegistration",
                                        "downloadETicket",
                                        "NewRegistration",
                                        "registrants",
                                        "evaluation",
                                        "newEvaluation",
                                        "viewMyEvaluation"]
            self._notify('confDisplaySMFillOrderedKeys', self._linkDataOrderedKeys)

    def getLinkData(self):
        return self._linkData
    def getLinkDataOrderedKeys(self):
        self.__init__() #init self._linkDataOrderedKeys if it isn't defined.
        return self._linkDataOrderedKeys


class ExternLink(Link):
    """
    class for link create by the user to a fixed link
    """
    Type = "extern"
    def __init__(self, name, URL):
        Link.__init__(self, name)
        self._URL = URL

    def clone(self, newMenu):
        newLink = ExternLink(self.getName(),self.getURL())
        newLink.setId(self.getId())
        newLink.setParent(newMenu)
        newLink.setEnabled(self.isEnabled())
        newLink.setCaption(self.getCaption())
        newLink.setDisplayTarget(self.getDisplayTarget())
        return newLink

    def getURL(self):
        return self._URL

    def setURL(self, URL):
        self._URL = URL

class PageLink(Link):
    """
    class for link create by the user to a fixed link
    """
    Type = "page"

    def __init__(self, name, page):
        Link.__init__(self, name)
        self._page = page

    def clone(self, newMenu):
        conf = newMenu.getConference()
        intPagesMgr = internalPagesMgr.InternalPagesMgrRegistery().getInternalPagesMgr(conf)
        newPage = self.getPage().clone(conf)
        intPagesMgr.addPage(newPage)
        newLink = PageLink(self.getName(),newPage)
        newLink.setId(self.getId())
        newLink.setParent(newMenu)
        newLink.setEnabled(self.isEnabled())
        newLink.setCaption(self.getCaption())
        newLink.setDisplayTarget(self.getDisplayTarget())
        return newLink

    def setPage(self, page):
        self._page=page

    def getPage(self):
        return self._page

    def getURL(self):
        return urlHandlers.UHInternalPageDisplay.getURL(self._page)


class _FormatDefaultData:

    def __init__(self):
        self._data={
            "titleBgColor":{"code":"",\
                            "url":urlHandlers.UHConfModifFormatTitleBgColor}, \
            "titleTextColor":{"code":"",\
                              "url":urlHandlers.UHConfModifFormatTitleTextColor}
            }

    def getColor(self,key):
        return self._data[key]["code"]

    def getURL(self,key):
        return self._data[key]["url"]


class Format(Persistent):

    def __init__(self):
        self._data={}
        self._data["titleBgColor"]=_FormatDefaultData().getColor("titleBgColor")
        self._data["titleTextColor"]=_FormatDefaultData().getColor("titleTextColor")
        self._p_changed = 1

    def getFormatOption(self,key):
        if self._data.has_key(key):
            code=self._data[key]
            url=_FormatDefaultData().getURL(key)
            return {"code":code,"url":url}
        return None

    def clone(self, newCdm):
        newFormat = newCdm.getFormat()
        newFormat.setColorCode("titleBgColor", self.getFormatOption("titleBgColor")["code"])
        newFormat.setColorCode("titleTextColor", self.getFormatOption("titleTextColor")["code"])
        return newFormat

    def setColorCode(self,key,color):
        if self._data.has_key(key):
            color=self._getCorrectColor(color)
            if color is None:
                return

            self._data[key]=color
            self._p_changed = 1

    def _getCorrectColor(self, color):
        if color == "":
            return ""

        if not color.startswith("#"):
            color = "#%s"%color
        m = re.match("^#[0-9A-Fa-f]{6}$", color)
        if m:
            return color
        return None

    def clearColorCode(self,key):
        self.setColorCode(key, "")

class TickerTape(Persistent):

    def __init__(self):
        # active will be set to true everytime the now
        # happening is enabled or the setText is called
        # this to avoid having an extra button in the interface
        # for activating the TickerTape
        self._active = False
        self._text=""
        self._enabledNowPlaying = False
        self._enabledSimpleText = False

    def clone(self, newCdm):
        newTT = newCdm.getTickerTape()
        newTT.setText(self.getText())
        newTT.setActive(self.isActive())
        newTT.setNowHappeningEnabled(self.isNowHappeningEnabled())
        newTT.setSimpleTextEnabled(self.isSimpleTextEnabled())
        return newTT

    def getText(self):
        return self._text

    def setText(self, text):
        self._active=True
        self._text = text

    def isActive(self):
        return self._active

    def activate(self):
        self._active=True

    def deactivate(self):
        self._active=False

    def setActive(self, v):
        self._active=v

    def isNowHappeningEnabled(self):
        try:
            if self._enabledNowPlaying:
                pass
        except AttributeError, e:
            self._enabledNowPlaying=False
        return self._enabledNowPlaying and self._active

    def setNowHappeningEnabled(self, v):
        self._active = True
        self._enabledNowPlaying = v

    def isSimpleTextEnabled(self):
        try:
            if self._enabledSimpleText:
                pass
        except AttributeError, e:
            self._enabledSimpleText = False
        return self._enabledSimpleText and self._active

    def setSimpleTextEnabled(self, v):
        self._active = True
        self._enabledSimpleText=v

class ImageWrapper(Persistent):
    """
    It wraps a LocalFile class, just in case we need to add more info to this image
    in the future.
    """

    def __init__(self, localFile):
        self._localFile = localFile

    def getId(self):
        return self._localFile.getId()

    def delete(self):
        self._localFile.delete()

    def getLocator(self):
        loc = self._localFile.getOwner().getLocator()
        loc["picId"] = self.getId()
        loc["picExt"] = self._localFile.getFileType().lower()
        return loc

    def clone(self):
        lf = self.getLocalFile().clone()
        iw = ImageWrapper(lf)
        return iw

    def getLocalFile(self):
        return self._localFile

class ImagesManager(Persistent):
    """
    This class manages all the images and pics used by a conference while displaying.
    We make difference between the "logo" of the conference and the rest of pictures.
    """

    def __init__(self, conf):
        self._conf = conf
        self._logo = None
        self._picList = {}
        self._picsCounter = Counter()

    def clone(self, newCdm):
        newIM = newCdm.getImagesManager()
        newIM._conf = newCdm.getConference()

        for pic in self.getPicList().values():
            lf = pic.getLocalFile()
            f = LocalFile()
            f.setFileName( lf.getFileName() )
            f.setFilePath( lf.getFilePath() )
            newIM.addPic(f)

        #Logo is not being cloned so far.

        return newIM

    def notifyModification(self):
        self._p_changed = 1

    def getPicList(self):
        """ function for getting piclist """
        try:
            if self._picList:
                pass
        except:
            self._picList = {}
        return self._picList

    def _getPicsCounter(self):
        try:
            if self._picsCounter:
                pass
        except:
            self._picsCounter = Counter()
        return self._picsCounter

    def addPic( self, picFile ):
        """ function for adding new picture item """
        picId = self._getPicsCounter().newCount()
        if self.getPicList().has_key(picId) and self.getPicList()[picId] != None:
            raise MaKaCError("there is already a pic with the id %s"%picId)
        picFile.setOwner( self._conf )
        picFile.setId( picId )
        picFile.archive( self._conf._getRepository() )
        pic = ImageWrapper(picFile)
        self.getPicList()[picId] = pic
        self.notifyModification()
        return pic

    def getPic( self,picId ):
        if self.getPicList().has_key(picId):
            return self.getPicList()[picId]
        return None

    def removePic(self,picId):
        """ function for removing pictures, used in picture uploader """
        pic = self.getPic(picId)
        if pic is not None:
            self.getPicList()[picId].delete()
            del self.getPicList()[picId]
        self.notifyModification()

    # Logo should be migrated to this class in the near future.
    def setLogo( self, logoFile ):
        logoFile.setOwner( self._conf )
        logoFile.setId( "logo" )
        logoFile.archive( self._conf._getRepository() )
        if self._logo != None:
            self._logo.delete()
        self._logo = logoFile

    def getLogo( self ):
        return self._logo

    def getLogoURL( self ):
        try:
            if self._logo == None:
                return ""
            return self._logo.getURL()
        except AttributeError:
            self._logo = None
            return ""

    def removeLogo(self):
        if self._logo is None:
            return
        self._logo.delete()
        self._logo = None

    def recoverLogo(self, logo):
        logo.setOwner(self._conf)
        if self._logo != None:
            self._logo.delete()
        self._logo = logo
        logo.recover()

class CSSWrapper(Persistent):
    """
    This class will handle the CSS file that is going to be applied
    to the conference display. CSS file can be an upload file or a
    template we already have. The upload file is an object of the class
    LocalFile and the template is just a string with the id (name) of the
    template.
    The class encapsulates the CSS so the user does not care about if it is
    a template or a local file.
    """

    def __init__(self, conf, css):
        self._conf = conf
        self._localFile = css

    def getId(self):
        return self._localFile.getId()

    def getLocator(self):
        loc = self._localFile.getOwner().getLocator()
        loc["cssId"] = self.getId()
        return loc

    def clone(self, newSM):
        f=None
        if self._localFile:
            f = LocalFile()
            f.setFileName( self._localFile.getFileName() )
            f.setFilePath( self._localFile.getFilePath() )
            f.setOwner( newSM._conf )
            f.setId( "css" )
            f.archive( newSM._conf._getRepository() )
        newCW = CSSWrapper(self._conf, f)
        return newCW

    def getURL(self):
        from MaKaC.webinterface.urlHandlers import UHConferenceCSS
        return UHConferenceCSS.getURL(self._conf)

    def getFileName(self, extension=True):
        fn =self._localFile.getFileName()
        if not extension:
            fn = fn.lower().replace(".css","")
        return fn

    def getFilePath(self):
        return self._localFile.getFilePath()

    def getSize(self):
        return self._localFile.getSize()

    def readBin(self):
        return self._localFile.readBin()

    def delete(self):
        self._localFile.delete()
        self._localFile=None

class StyleManager(Persistent):
    """
    This class manages the CSS customization for a conference.
    """

    def __init__(self, conf):
        self._conf = conf
        self._css = None
        self._usingTemplate = None

    def clone(self, newCdm):
        newSM = newCdm.getStyleManager()
        newSM._conf = newCdm.getConference()
        newSM._usingTemplate = self._usingTemplate
        if self._css:
            newSM._css = self._css.clone(newSM)

        #Logo is not being cloned so far.

        return newSM

    def isUsingTemplate(self):
        return self._usingTemplate is not None

    def useLocalCSS(self):
        self._usingTemplate = None

    def setCSS( self, cssFile ):
        if isinstance(cssFile, str):
            # we will use a template but we keep the uploaded css file
            from indico.modules import ModuleHolder
            self._cssTplsModule = ModuleHolder().getById("cssTpls")
            self._usingTemplate = self._cssTplsModule.getCssTplById(cssFile)
        else:
            # uploaded file
            cssFile.setOwner( self._conf )
            cssFile.setId( "css" )
            cssFile.archive( self._conf._getRepository() )
            if self._css != None:
                self._css.delete()
            self._usingTemplate = None
            self._css = CSSWrapper(self._conf, cssFile)

    def getLocalCSS( self ):
        return self._css

    def getCSS(self):
        if self._usingTemplate:
            return self._usingTemplate
        return self.getLocalCSS()

    def getCSSURL( self ):
        if self.getCSS():
            return self.getCSS().getURL()
        return None

    def removeCSS(self):
        if self._css is not None:
            self._css.delete()
            self._css = None

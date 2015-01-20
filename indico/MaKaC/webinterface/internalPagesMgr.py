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
from MaKaC.webinterface import urlHandlers

class InternalPagesMgrRegistery:
    """
    Class to get the InternalPagesMgr for a conference
    """

    def __init__(self):
        self._pagesMgrRegistery = None

    def _getInternalPagesMgrRegistery( self ):
        #DBMgr.getInstance().commit()
        if not self._pagesMgrRegistery:
            db_root = DBMgr.getInstance().getDBConnection().root()
            if db_root.has_key( "internalPagesRegistery" ):
                self._pagesMgrRegistery = db_root["internalPagesRegistery"]
            else:
                self._pagesMgrRegistery = OOBTree.OOBTree()
                db_root["internalPagesRegistery"] = self._pagesMgrRegistery
        return self._pagesMgrRegistery


    def registerInternalPagesMgr( self, conference, intPagesMgr ):
        """Associates a given conference with a confDispplayMgr
        """
        self._getInternalPagesMgrRegistery()[ conference.getId() ] = intPagesMgr

    def getInternalPagesMgr( self, conference):
        """Gives back the webfactory associated with a given conference or None
            if no association exists
        """
        if self._getInternalPagesMgrRegistery().has_key( conference.getId() ):
            ipm = self._getInternalPagesMgrRegistery()[ conference.getId() ]
        else:
            ipm = InternalPagesMgr(conference)
            self.registerInternalPagesMgr(conference, ipm)
        return ipm


class InternalPagesMgr(Persistent):
    """
    base class for the InternalPagesMgr object
    """

    def __init__(self, conf):
        self._conf=conf
        self._pages={}
        self._pagesGenerator=Counter()

    def getConference(self):
        return self._conf

    def _generateNewPageId( self ):
        """Returns a new unique identifier for a page
        """
        return str(self._pagesGenerator.newCount())

    def getPagesList(self):
        return self._pages.values()

    def addPage(self, page):
        if page.getId()=="":
            page.setId(self._generateNewPageId())
        self._pages[page.getId()]=page
        self.notifyModification()

    def removePage(self, page):
        if self._pages.has_key(page.getId()):
            self._pages.pop(page.getId())
            self.notifyModification()

    def getPageById(self, id):
        if self._pages.has_key(id):
            return self._pages[id]
        else:
            return None

    def notifyModification(self):
        self._p_changed=1

class InternalPage(Persistent):

    def __init__(self, conf):
        self._conf=conf
        self._id=""
        self._title=""
        self._content=""
        self._isHome=False

    def clone(self, conf):
        newPage = InternalPage(conf)
        newPage.setContent(self.getContent())
        newPage.setTitle(self.getTitle())
        newPage.setHome(self.isHome())
        return newPage

    def isHome(self):
        try:
            return self._isHome
        except:
            self._isHome=False
            return self._isHome

    def setHome(self, isHome=False):
        self._isHome=isHome

    def getConference(self):
        return self._conf

    def getId(self):
        return self._id

    def setId(self, id):
        self._id=id

    def getContent(self):
        return self._content

    def setContent(self, c):
        self._content=c

    def getTitle(self):
        return self._title

    def setTitle(self, title):
        self._title=title

    def getLocator( self ):
        """Gives back a globaly unique identification encapsulated in a Locator
            object for the internal page instance
        """
        if self._conf == None:
            loc=Locator()
        loc=self.getConference().getLocator()
        loc["pageId"]=self.getId()
        return loc

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

from datetime import timedelta
from persistent import Persistent
from MaKaC.common.Counter import Counter
import MaKaC.modules.base as modules
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.i18n import _
from MaKaC.common.timezoneUtils import getAdjustedDate, nowutc, isTimezoneAware,\
    setAdjustedDate
from MaKaC.common.PickleJar import Retrieves
from MaKaC.common.Conversion import Conversion
from MaKaC.modules.base import ModulesHolder

class NewsModule(modules.Module):
    """
    This module holds all the information needed to keep the news in Indico.
    That means all the news items and other related information.

    _newsTypes is a tuple with 2 values: id, label. Keep the order as it will appear in the display interface.
    """
    id = "news"
    _newsTypes = [ ("general", _("General News") ), ("future", _("Coming soon") ), ("new", _("New features") ), ("bug", _("Bug fixes") ) ]

    def __init__(self):
        self._newsItems = []
        self._p_changed = 1
        self._newsCounter = Counter()
        self._recentDays = 14 #days to keep a 'New' tag on recent news items
        # fetch all news from the previous location.
        self.addNewsItem(NewsItem( _("Previous news"), HelperMaKaCInfo.getMaKaCInfoInstance().getNews(), "general"))

    def getNewsItemsList(self):
        return self._newsItems

    def addNewsItem(self, news):
        news.setId(self._newsCounter.newCount())
        self._newsItems.insert(0,news)
        self._p_changed = 1

    def removeNewsItem(self, id):
        item=self.getNewsItemById(id)
        if item:
            self._newsItems.remove(item)
            self._p_changed = 1
        else:
            raise Exception(_("News item does not exist"))

    def getNewsItemById(self, id):
        for new in self._newsItems:
            if new.getId() == id:
                return new
        return None

    def getRecentDays(self):
        if not hasattr(self, '_recentDays'):
            self._recentDays = 14
        return self._recentDays

    def setRecentDays(self, recentDays):
        self._recentDays = recentDays

    @classmethod
    def getNewsTypes(self):
        return NewsModule._newsTypes

    @classmethod
    def getNewsTypesAsDict(self):
        return dict(NewsModule._newsTypes)
    
class NewsItem(Persistent):
    
    def __init__(self, title = "", content="", type = ""):
        self._id = None
        self._creationDate = nowutc()
        self._content=content
        self._title = title
        self._type = type
        self._new = True

    @Retrieves(['MaKaC.modules.news.NewsItem'], 'id')
    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id

    def getCreationDate(self):
        if not isTimezoneAware(self._creationDate):
            self._creationDate = setAdjustedDate(self._creationDate, tz = 'UTC')
        return self._creationDate

    @Retrieves(['MaKaC.modules.news.NewsItem'], 'creationDate', Conversion.datetime)
    def getAdjustedCreationDate(self, tz = 'UTC'):
        return getAdjustedDate(self.getCreationDate(), tz = tz)

    @Retrieves(['MaKaC.modules.news.NewsItem'], 'text')
    def getContent(self):
        return self._content

    def setContent(self, content):
        self._content=content

    @Retrieves(['MaKaC.modules.news.NewsItem'], 'title')
    def getTitle(self):
        return self._title

    def setTitle(self, title):
        self._title = title

    @Retrieves(['MaKaC.modules.news.NewsItem'], 'type')
    def getType(self):
        return self._type

    def setType(self, type):
        self._type = type

    @Retrieves(['MaKaC.modules.news.NewsItem'], 'humanReadableType')
    def getHumanReadableType(self):
        return NewsModule.getNewsTypesAsDict()[self._type]

    def isNew(self):
        newsModule = ModulesHolder().getById("news")
        return self.getCreationDate() + timedelta(days = newsModule.getRecentDays()) > nowutc()

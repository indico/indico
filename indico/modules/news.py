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

from datetime import timedelta
from persistent import Persistent
from MaKaC.common.Counter import Counter
from indico.modules import ModuleHolder, Module
from MaKaC.common.info import HelperMaKaCInfo
from indico.util.i18n import L_
from MaKaC.common.timezoneUtils import getAdjustedDate, nowutc, \
     isTimezoneAware, setAdjustedDate
from MaKaC.common.fossilize import Fossilizable, fossilizes
from MaKaC.fossils.modules import INewsItemFossil


class NewsModule(Module):
    """
    This module holds all the information needed to keep the news in Indico.
    That means all the news items and other related information.

    _newsTypes is a tuple with 2 values: id, label. Keep the order as it will
    appear in the display interface.
    """

    id = "news"
    _newsTypes = [ ("general", L_("General News") ), ("future", L_("Coming soon") ),
                   ("new", L_("New features") ), ("bug", L_("Bug fixes") ) ]

    def __init__(self):
        self._newsItems = []
        self._p_changed = 1
        self._newsCounter = Counter()
        # days to keep a 'New' tag on recent news items
        self._recentDays = 14
        # fetch all news from the previous location.
        self.addNewsItem(
            NewsItem(_("Previous news"),
                     HelperMaKaCInfo.getMaKaCInfoInstance().getNews(),
                     "general"))

    def getNewsItemsList(self):
        return self._newsItems

    def addNewsItem(self, news):
        news.setId(self._newsCounter.newCount())
        self._newsItems.insert(0, news)
        self._p_changed = 1

    def removeNewsItem(self, id):
        item = self.getNewsItemById(id)
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


class NewsItem(Persistent, Fossilizable):

    fossilizes(INewsItemFossil)

    def __init__(self, title="", content="", type=""):
        self._id = None
        self._creationDate = nowutc()
        self._content = content
        self._title = title
        self._type = type
        self._new = True

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id

    def getCreationDate(self):
        if not isTimezoneAware(self._creationDate):
            self._creationDate = setAdjustedDate(self._creationDate, tz = 'UTC')
        return self._creationDate

    def getAdjustedCreationDate(self, tz='UTC'):
        return getAdjustedDate(self.getCreationDate(), tz=tz)

    def getContent(self):
        return self._content

    def setContent(self, content):
        self._content = content

    def getTitle(self):
        return self._title

    def setTitle(self, title):
        self._title = title

    def getType(self):
        return self._type

    def setType(self, type):
        self._type = type

    def getHumanReadableType(self):
        return NewsModule.getNewsTypesAsDict()[self._type]

    def isNew(self):
        newsModule = ModuleHolder().getById("news")
        return self.getCreationDate() + \
               timedelta(days=newsModule.getRecentDays()) > nowutc()

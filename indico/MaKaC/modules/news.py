# -*- coding: utf-8 -*-
##
## $Id: news.py,v 1.4 2009/06/26 08:45:30 cangelov Exp $
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

from persistent import Persistent
from datetime import datetime
from MaKaC.common.Counter import Counter
import MaKaC.modules.base as modules
from MaKaC.common.info import HelperMaKaCInfo

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

    @classmethod
    def getNewsTypes(self):
        return NewsModule._newsTypes


    @classmethod
    def getNewsTypesAsDict(self):
        return dict(NewsModule._newsTypes)
    
class NewsItem(Persistent):
    
    def __init__(self, title = "", content="", type = ""):
        self._id = None
        self._creationDate=datetime.utcnow()
        self._content=content
        self._title = title
        self._type = type

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id

    def getCreationDate(self):
        return self._creationDate

    def getContent(self):
        return self._content


    def setContent(self, content):
        self._content=content

    def getTitle(self):
        return self._title

    def setTitle(self, title):
        self._title = title

    def getType(self):
        return self._type

    def setType(self, type):
        self._type = type
        








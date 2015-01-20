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

from MaKaC.services.implementation.base import ParameterManager,\
    TextModificationBase
from MaKaC.services.implementation.base import AdminService

from MaKaC.common.utils import formatDateTime
from MaKaC.services.interface.rpc.common import ServiceError

from MaKaC.fossils.modules import INewsItemFossil

from indico.modules import ModuleHolder, news

class NewsRecentDays(TextModificationBase, AdminService):
    """ Set number of days that a news item is considered recent
    """
    def _handleSet(self):
        newDays = self._value
        try:
            newDays = int(self._value)
        except ValueError, e:
            raise ServiceError('ERR-NEWS0', 'Recent days value has to be an interger', e)

        newsModule = ModuleHolder().getById("news")
        newsModule.setRecentDays(newDays)

    def _handleGet(self):
        newsModule = ModuleHolder().getById("news")
        return newsModule.getRecentDays()

class NewsAdd(AdminService):

    def _checkParams(self):
        AdminService._checkParams(self)

        pm = ParameterManager(self._params)

        self._title = pm.extract("title", pType=str, allowEmpty=False)
        self._type = pm.extract("type", pType=str, allowEmpty=False)
        self._content = pm.extract("content", pType=str, allowEmpty=True)

    def _getAnswer(self):
        newsModule=ModuleHolder().getById("news")
        ni = news.NewsItem(self._title, self._content, self._type)
        newsModule.addNewsItem(ni)
        tz = self.getAW().getUser().getTimezone() #this is an admin service so user is always logged in (or _checkProtection detects it before)
        return ni.fossilize(INewsItemFossil, tz=tz)

class NewsDelete(AdminService):

    def _checkParams(self):
        AdminService._checkParams(self)

        pm = ParameterManager(self._params)

        self._id = pm.extract("id", pType=str, allowEmpty=False)

    def _getAnswer(self):
        newsModule=ModuleHolder().getById("news")
        newsModule.removeNewsItem(self._id)

class NewsSave(AdminService):

    def _checkParams(self):
        AdminService._checkParams(self)

        pm = ParameterManager(self._params)

        self._id = pm.extract("id", pType=str, allowEmpty=False)
        self._title = pm.extract("title", pType=str, allowEmpty=False)
        self._type = pm.extract("type", pType=str, allowEmpty=False)
        self._content = pm.extract("content", pType=str, allowEmpty=True)

    def _getAnswer(self):
        newsModule=ModuleHolder().getById("news")
        item=newsModule.getNewsItemById(self._id)
        if item:
            item.setTitle(self._title)
            item.setType(self._type)
            item.setContent(self._content)
            tz = self.getAW().getUser().getTimezone() #this is an admin service so user is always logged in (or _checkProtection detects it before)
            return item.fossilize(INewsItemFossil, tz=tz)
        else:
            raise Exception("News item does not exist")


methodMap = {
    "setRecentDays": NewsRecentDays,
    "add": NewsAdd,
    "delete": NewsDelete,
    "save": NewsSave
    }


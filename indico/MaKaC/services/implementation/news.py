from MaKaC.services.implementation.base import ParameterManager
from MaKaC.services.implementation.base import AdminService

import MaKaC.webinterface.locators as locators
from MaKaC import conference
from MaKaC.modules.base import ModulesHolder
from MaKaC.modules.news import NewsItem
from MaKaC.common.utils import formatDateTime

class NewsAdd(AdminService):

    def _checkParams(self):
        AdminService._checkParams(self)

        pm = ParameterManager(self._params)

        self._title = pm.extract("title", pType=str, allowEmpty=False)
        self._type = pm.extract("type", pType=str, allowEmpty=False)
        self._text = pm.extract("content", pType=str, allowEmpty=True)

    def _getAnswer(self):

        newsModule=ModulesHolder().getById("news")
        ni=NewsItem(self._title, self._text, self._type)
        newsModule.addNewsItem(ni)
        return {"creationDate":formatDateTime(ni.getCreationDate()), "title":self._title, "type": self._type, "content":self._text, "id":ni.getId()}

class NewsDelete(AdminService):

    def _checkParams(self):
        AdminService._checkParams(self)

        pm = ParameterManager(self._params)

        self._id = pm.extract("id", pType=str, allowEmpty=False)

    def _getAnswer(self):
        newsModule=ModulesHolder().getById("news")
        newsModule.removeNewsItem(self._id)

class NewsSave(AdminService):

    def _checkParams(self):
        AdminService._checkParams(self)

        pm = ParameterManager(self._params)

        self._id = pm.extract("id", pType=str, allowEmpty=False)
        self._title = pm.extract("title", pType=str, allowEmpty=False)
        self._type = pm.extract("type", pType=str, allowEmpty=False)
        self._text = pm.extract("content", pType=str, allowEmpty=True)

    def _getAnswer(self):
        newsModule=ModulesHolder().getById("news")
        item=newsModule.getNewsItemById(self._id)
        if item:
            item.setTitle(self._title)
            item.setType(self._type)
            item.setContent(self._text)
            return {"creationDate":formatDateTime(item.getCreationDate()), "title":self._title, "type":self._type, "content":self._text, "id":item.getId()}
        else:
            raise Exception("News item does not exist")


methodMap = {
    "add": NewsAdd,
    "delete": NewsDelete,
    "save": NewsSave
    }


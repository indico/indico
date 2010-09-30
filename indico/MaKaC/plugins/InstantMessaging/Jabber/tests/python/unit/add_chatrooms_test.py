from MaKaC import conference
import unittest
#from indico.tests.env import *

from datetime import datetime
from pytz import timezone
from MaKaC.user import Avatar, AvatarHolder

from MaKaC.conference import Conference, ConferenceHolder
from MaKaC.plugins.InstantMessaging.handlers import *
from MaKaC.plugins.helpers import DBHelpers
from MaKaC.plugins.base import Observable, PluginsHolder

from MaKaC.common.db import DBMgr


def setup_module():
    DBMgr.getInstance().startRequest()
    PluginsHolder().loadAllPlugins()
    PluginsHolder().getPluginType('InstantMessaging').setActive(True)
    PluginsHolder().getPluginType('InstantMessaging').getPlugin('Jabber').setActive(True)
    PluginsHolder().getComponentsManager().registerAllComponents()

def teardown_module():
    DBMgr.getInstance().abort()
    DBMgr.getInstance().endRequest()


#From testCategories.py
class TestAddRemoveCR(unittest.TestCase, Observable):

    def testBasicAddRemoveCR(self):
        dbRoot = DBMgr.getInstance().getDBConnection().root()['plugins']['InstantMessaging'].getPlugin('Jabber').getStorage()

        u=AvatarHolder().getById('0')

        c1=conference.Conference(u)
        c1.setId("1")

        c2=conference.Conference(u)
        c2.setId("2")

        self._conference = c1.getId()
        self._conferenceID = c1.getId()

        #for the first conference
        cr1 = Chatroom('chatroom1', u, c1, None)
        cr2 = Chatroom('chatroom2', u, c1, None)
        cr3 = Chatroom('chatroom3', u, c1, None)


        #for the second conference
        cr4 = Chatroom('chatroom4', u, c2, None)
        cr5 = Chatroom('chatroom5', u, c2, None)
        cr6 = Chatroom('chatroom6', u, c2, None)


        #insert them in the database
        self._notify('createChatroom', cr1)
        self._notify('createChatroom', cr2)
        self._notify('createChatroom', cr3)
        self._notify('createChatroom', cr4)
        self._notify('createChatroom', cr5)
        self._notify('createChatroom', cr6)

        cr1ID = cr1.getId()
        cr2ID = cr2.getId()
        cr3ID = cr3.getId()
        cr4ID = cr4.getId()
        cr5ID = cr5.getId()
        cr6ID = cr6.getId()

        #checks for indexByConf
        assert (len(DBHelpers.getChatroomList(c1))==3)
        assert (len(DBHelpers.getChatroomList(c2))==3)

        #checks for indexByID
        assert(DBHelpers.getChatroom(cr1ID).getId()==cr1ID)
        assert(DBHelpers.getChatroom(cr2ID).getId()==cr2ID)
        assert(DBHelpers.getChatroom(cr3ID).getId()==cr3ID)
        assert(DBHelpers.getChatroom(cr4ID).getId()==cr4ID)
        assert(DBHelpers.getChatroom(cr5ID).getId()==cr5ID)
        assert(DBHelpers.getChatroom(cr6ID).getId()==cr6ID)

        #insert created chatrooms
        self._conference = c2.getId()
        cr1 = DBHelpers.getChatroom(cr1ID)
        cr1.setConference(c2)
        self._notify('addConference2Room', cr1)
        cr2 = DBHelpers.getChatroom(cr2ID)
        cr2.setConference(c2)
        self._notify('addConference2Room', cr2)
        cr3 = DBHelpers.getChatroom(cr3ID)
        cr3.setConference(c2)
        self._notify('addConference2Room', cr3)

        self._conference = c1.getId()
        cr4 = DBHelpers.getChatroom(cr4ID)
        cr4.setConference(c1)
        self._notify('addConference2Room', cr4)
        cr5 = DBHelpers.getChatroom(cr5ID)
        cr5.setConference(c1)
        self._notify('addConference2Room', cr5)
        cr6 = DBHelpers.getChatroom(cr6ID)
        cr6.setConference(c1)
        self._notify('addConference2Room', cr6)

        #checks for conference dictionary inside each Chatroom object
        assert(len(dbRoot['indexByUser'][u.getId()])==6)
        for cr in dbRoot['indexByUser'][u.getId()]:
            assert(len(DBHelpers.getChatroom(cr.getId()).getConferences())==2)

        names = {cr1.getTitle():'chatroom1', cr2.getTitle():'chatroom2', cr3.getTitle():'chatroom3', cr4.getTitle():'chatroom4', cr5.getTitle():'chatroom5', cr6.getTitle():'chatroom6'}
        assert(len(dbRoot['indexByCRName'])==6)
        for cr in dbRoot['indexByCRName']:
            #the name of the index is what we expect
            assert(cr == list(dbRoot['indexByCRName'][cr])[0].getTitle())
            #the name is one of the expected ones
            assert(cr in names)
            names.pop(cr)

        #delete rooms and see
        self._conferenceID = c1.getId()
        self._notify('deleteChatroom', cr3)
        self._notify('deleteChatroom', cr1)
        #conferences inside the chat rooms are consistent
        assert( len(DBHelpers.getChatroom(cr3ID).getConferences())==1 and DBHelpers.getChatroom(cr3ID).getConferences().has_key(c2.getId()) )
        assert( len(DBHelpers.getChatroom(cr1ID).getConferences())==1 and DBHelpers.getChatroom(cr1ID).getConferences().has_key(c2.getId()) )

        cr3.setTitle('editedRoom')
        cr3.setDescription('ou yeh')
        self._notify('editChatroom', {'oldTitle': 'chatroom3', 'newRoom':cr3})
        assert( dbRoot['indexByCRName'].has_key('editedRoom') and not dbRoot['indexByCRName'].has_key('chatroom3'))

        #consistent in indexByConf
        assert(DBHelpers.getChatroomList(c2).has_key(cr3) and not DBHelpers.getChatroomList(c1).has_key(cr3))
        assert(DBHelpers.getChatroomList(c2).has_key(cr1) and not DBHelpers.getChatroomList(c1).has_key(cr1))

        #consistent in indexByID
        assert(len(dbRoot['indexByID'])==6)

        #consistent in indexByCRName
        assert(dbRoot['indexByCRName'].has_key(cr3.getTitle()))
        assert(dbRoot['indexByCRName'].has_key(cr1.getTitle()))

        #consistent in indexByUser
        assert(len(dbRoot['indexByUser']['0'])==6)


        self._conferenceID = c2.getId()
        self._notify('deleteChatroom', cr6)
        self._notify('deleteChatroom', cr2)
        self._notify('deleteChatroom', cr5)
        #conferences inside the chat rooms are consistent
        assert( len(DBHelpers.getChatroom(cr6ID).getConferences())==1 and DBHelpers.getChatroom(cr6ID).getConferences().has_key(c1.getId()) )
        assert( len(DBHelpers.getChatroom(cr2ID).getConferences())==1 and DBHelpers.getChatroom(cr2ID).getConferences().has_key(c1.getId()) )
        assert( len(DBHelpers.getChatroom(cr5ID).getConferences())==1 and DBHelpers.getChatroom(cr5ID).getConferences().has_key(c1.getId()) )

        #consistent in indexByConf
        assert(DBHelpers.getChatroomList(c1).has_key(cr6) and not DBHelpers.getChatroomList(c2).has_key(cr6))
        assert(DBHelpers.getChatroomList(c1).has_key(cr2) and not DBHelpers.getChatroomList(c2).has_key(cr2))
        assert(DBHelpers.getChatroomList(c1).has_key(cr5) and not DBHelpers.getChatroomList(c2).has_key(cr5))

        #consistent in indexByID
        assert(len(dbRoot['indexByID'])==6)

        #consistent in indexByCRName
        assert(dbRoot['indexByCRName'].has_key(cr6.getTitle()))
        assert(dbRoot['indexByCRName'].has_key(cr2.getTitle()))
        assert(dbRoot['indexByCRName'].has_key(cr5.getTitle()))

        #consistent in indexByUser
        assert(len(dbRoot['indexByUser']['0'])==6)

        self._conferenceID = c1.getId()
        self._notify('deleteChatroom', cr4)
        self._notify('deleteChatroom', cr2)
        self._notify('deleteChatroom', cr5)
        self._notify('deleteChatroom', cr6)
        #conferences inside the chat rooms are consistent
        assert( len(DBHelpers.getChatroom(cr4ID).getConferences())==1 and DBHelpers.getChatroom(cr4ID).getConferences().has_key(c2.getId()) )

        #consistent in indexByConf
        assert(DBHelpers.getChatroomList(c2).has_key(cr4) and not dbRoot['indexByConf'].has_key(c1))
        assert(not DBHelpers.getChatroomList(c2).has_key(cr2))
        assert(not DBHelpers.getChatroomList(c2).has_key(cr5))
        assert(not DBHelpers.getChatroomList(c2).has_key(cr6))

        #consistent in indexByID
        assert(len(dbRoot['indexByID'])==3)

        #consistent in indexByCRName
        assert(dbRoot['indexByCRName'].has_key(cr4.getTitle()))
        assert(not dbRoot['indexByCRName'].has_key(cr2.getTitle()))
        assert(not dbRoot['indexByCRName'].has_key(cr5.getTitle()))
        assert(not dbRoot['indexByCRName'].has_key(cr6.getTitle()))

        #consistent in indexByUser
        assert(len(dbRoot['indexByUser']['0'])==3)

        self._conferenceID = c2.getId()
        self._notify('deleteChatroom', cr1)
        self._notify('deleteChatroom', cr3)
        self._notify('deleteChatroom', cr4)
        #consistent in indexByConf
        assert(not dbRoot['indexByConf'].has_key(c2))

        #consistent in indexByID
        assert(len(dbRoot['indexByID'])==0)

        #consistent in indexByCRName
        assert(not dbRoot['indexByCRName'].has_key(cr6.getTitle()))
        assert(not dbRoot['indexByCRName'].has_key(cr2.getTitle()))
        assert(not dbRoot['indexByCRName'].has_key(cr5.getTitle()))

        #consistent in indexByUser
        assert(not dbRoot['indexByUser'].has_key('0'))
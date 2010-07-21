from MaKaC import conference
import unittest
#from indico.tests.env import *

from datetime import datetime
from pytz import timezone
from MaKaC.user import Avatar, AvatarHolder

from MaKaC.conference import Conference, ConferenceHolder
from MaKaC.plugins.InstantMessaging.handlers import *
from MaKaC.plugins.base import Observable

from MaKaC.common.db import DBMgr


def setup_module():
    DBMgr.getInstance().startRequest()

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
        cr1ID = cr1.getId()
        cr2 = Chatroom('chatroom2', u, c1, None)
        cr2ID = cr2.getId()
        cr3 = Chatroom('chatroom3', u, c1, None)
        cr3ID = cr3.getId()

        #for the second conference
        cr4 = Chatroom('chatroom4', u, c2, None)
        cr4ID = cr4.getId()
        cr5 = Chatroom('chatroom5', u, c2, None)
        cr5ID = cr5.getId()
        cr6 = Chatroom('chatroom6', u, c2, None)
        cr6ID = cr6.getId()

        #insert them in the database
        self._notify('createChatroom', cr1)
        self._notify('createChatroom', cr2)
        self._notify('createChatroom', cr3)
        self._notify('createChatroom', cr4)
        self._notify('createChatroom', cr5)
        self._notify('createChatroom', cr6)

        #checks for indexByConf
        assert (len(DBUtils.getChatroomList(c1))==3)
        assert (len(DBUtils.getChatroomList(c2))==3)

        #checks for indexByID
        assert(DBUtils.getChatroom(cr1).getId()==cr1ID)
        assert(DBUtils.getChatroom(cr2).getId()==cr2ID)
        assert(DBUtils.getChatroom(cr3).getId()==cr3ID)
        assert(DBUtils.getChatroom(cr4).getId()==cr4ID)
        assert(DBUtils.getChatroom(cr5).getId()==cr5ID)
        assert(DBUtils.getChatroom(cr6).getId()==cr6ID)

        #insert created chatrooms
        self._conference = c2.getId()
        cr1 = DBUtils.getChatroom(cr1ID)
        cr1.setConference(ConferenceHolder().getById(c2))
        self._notify('addConference2Room', cr1)
        cr2 = DBUtils.getChatroom(cr2ID)
        cr2.setConference(ConferenceHolder().getById(c2))
        self._notify('addConference2Room', cr2)
        cr3 = DBUtils.getChatroom(cr3ID)
        cr3.setConference(ConferenceHolder().getById(c2))
        self._notify('addConference2Room', cr3)

        self._conference = c1.getId()
        cr4 = DBUtils.getChatroom(cr4ID)
        cr4.setConference(ConferenceHolder().getById(c1))
        self._notify('addConference2Room', cr4)
        cr5 = DBUtils.getChatroom(cr5ID)
        cr5.setConference(ConferenceHolder().getById(c1))
        self._notify('addConference2Room', cr5)
        cr6 = DBUtils.getChatroom(cr6ID)
        cr6.setConference(ConferenceHolder().getById(c1))
        self._notify('addConference2Room', cr6)

        #checks for conference dictionary inside each Chatroom object
        assert(len(dbRoot['indexByUser'][u.getId()])==6)
        for cr in dbRoot['indexByUser'][u.getId()]:
            assert(len(DBUtils.getChatroom(cr.getId()).getConferences())==2)

        names = ['chatroom1', 'chatroom2', 'chatroom3', 'chatroom4', 'chatroom5', 'chatroom6']
        assert(len(dbRoot['indexByCRName'])==6)
        for cr in dbRoot['indexByCRName']:
            #the name of the index is what we expect
            assert(cr == dbRoot['indexByCRName'][cr].getTitle())
            #the name is one of the expected ones
            assert(cr in names)
            names.pop(cr)

        #delete rooms and see
        self._conferenceID = c1.getId()
        self._notify('deleteChatroom', cr3)
        self._notify('deleteChatroom', cr1)
        #conferences inside the chat rooms are consistent
        assert( len(DBUtils.getChatroom(cr3ID).getConferences())==1 and DBUtils.getChatroom(cr3ID).getConferences().has_key(c2.getId()) )
        assert( len(DBUtils.getChatroom(cr1ID).getConferences())==1 and DBUtils.getChatroom(cr1ID).getConferences().has_key(c2.getId()) )

        #consistent in indexByConf
        assert(DBUtils.getChatroomList(c2).has_key(cr3ID) and not DBUtils.getChatroomList(c1).has_key(cr3ID))
        assert(DBUtils.getChatroomList(c2).has_key(cr1ID) and not DBUtils.getChatroomList(c1).has_key(cr1ID))

        #consistent in indexByID
        assert(len(dbRoot['indexByID'])==6)

        #consistent in indexByCRName
        assert(dbRoot['indexByCRName'].has_key(cr3.getTitle()))
        assert(dbRoot['indexByCRName'].has_key(cr1.getTitle()))

        #consistent in indexByUser
        assert(len(dbRoot['indexByUser'])==6)


        self._conferenceID = c2.getId()
        self._notify('deleteChatroom', cr6)
        self._notify('deleteChatroom', cr2)
        self._notify('deleteChatroom', cr5)
        #conferences inside the chat rooms are consistent
        assert( len(DBUtils.getChatroom(cr6ID).getConferences())==1 and DBUtils.getChatroom(cr6ID).getConferences().has_key(c1.getId()) )
        assert( len(DBUtils.getChatroom(cr2ID).getConferences())==1 and DBUtils.getChatroom(cr2ID).getConferences().has_key(c1.getId()) )
        assert( len(DBUtils.getChatroom(cr5ID).getConferences())==1 and DBUtils.getChatroom(cr5ID).getConferences().has_key(c1.getId()) )

        #consistent in indexByConf
        assert(DBUtils.getChatroomList(c1).has_key(cr6ID) and not DBUtils.getChatroomList(c2).has_key(cr6ID))
        assert(DBUtils.getChatroomList(c1).has_key(cr2ID) and not DBUtils.getChatroomList(c2).has_key(cr2ID))
        assert(DBUtils.getChatroomList(c1).has_key(cr5ID) and not DBUtils.getChatroomList(c2).has_key(cr5ID))

        #consistent in indexByID
        assert(len(dbRoot['indexByID'])==6)

        #consistent in indexByCRName
        assert(dbRoot['indexByCRName'].has_key(cr6.getTitle()))
        assert(dbRoot['indexByCRName'].has_key(cr2.getTitle()))
        assert(dbRoot['indexByCRName'].has_key(cr5.getTitle()))

        #consistent in indexByUser
        assert(len(dbRoot['indexByUser'])==6)

        self._conferenceID = c1.getId()
        self._notify('deleteChatroom', cr4)
        self._notify('deleteChatroom', cr2)
        self._notify('deleteChatroom', cr5)
        self._notify('deleteChatroom', cr6)
        #conferences inside the chat rooms are consistent
        assert( len(DBUtils.getChatroom(cr4ID).getConferences())==1 and DBUtils.getChatroom(cr4ID).getConferences().has_key(c2.getId()) )

        #consistent in indexByConf
        assert(DBUtils.getChatroomList(c2).has_key(cr4ID) and not DBUtils.getChatroomList(c1).has_key(cr4ID))
        assert(not DBUtils.getChatroomList(c2).has_key(cr2ID) and not DBUtils.getChatroomList(c1).has_key(cr2ID))
        assert(not DBUtils.getChatroomList(c2).has_key(cr5ID) and not DBUtils.getChatroomList(c1).has_key(cr5ID))
        assert(not DBUtils.getChatroomList(c2).has_key(cr6ID) and not DBUtils.getChatroomList(c1).has_key(cr6ID))

        #consistent in indexByID
        assert(len(dbRoot['indexByID'])==3)

        #consistent in indexByCRName
        assert(dbRoot['indexByCRName'].has_key(cr4.getTitle()))
        assert(not dbRoot['indexByCRName'].has_key(cr2.getTitle()))
        assert(not dbRoot['indexByCRName'].has_key(cr5.getTitle()))
        assert(not dbRoot['indexByCRName'].has_key(cr6.getTitle()))

        #consistent in indexByUser
        assert(len(dbRoot['indexByUser'])==3)

        self._conferenceID = c2.getId()
        self._notify('deleteChatroom', cr1)
        self._notify('deleteChatroom', cr3)
        self._notify('deleteChatroom', cr4)
        #consistent in indexByConf
        assert(not DBUtils.getChatroomList(c1).has_key(cr6ID) and not DBUtils.getChatroomList(c2).has_key(cr6ID))
        assert(not DBUtils.getChatroomList(c1).has_key(cr2ID) and not DBUtils.getChatroomList(c2).has_key(cr2ID))
        assert(not DBUtils.getChatroomList(c1).has_key(cr5ID) and not DBUtils.getChatroomList(c2).has_key(cr5ID))

        #consistent in indexByID
        assert(len(dbRoot['indexByID'])==0)

        #consistent in indexByCRName
        assert(not dbRoot['indexByCRName'].has_key(cr6.getTitle()))
        assert(not dbRoot['indexByCRName'].has_key(cr2.getTitle()))
        assert(not dbRoot['indexByCRName'].has_key(cr5.getTitle()))

        #consistent in indexByUser
        assert(len(dbRoot['indexByUser'])==0)
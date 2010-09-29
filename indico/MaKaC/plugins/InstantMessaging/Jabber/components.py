'''
Created on Jul 21, 2010

@author: cesar
'''
from MaKaC.plugins.notificationComponents import Component
from MaKaC.plugins.notificationComponents import IContributor
from MaKaC.plugins.notificationComponents import INavigationContributor
from MaKaC.plugins.notificationComponents import IListener
from MaKaC.plugins.notificationComponents import IInstantMessagingListener

from BTrees.OOBTree import OOBTree
from BTrees.OOBTree import OOTreeSet
from MaKaC.common.Counter import Counter
from MaKaC.webinterface import wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.plugins.InstantMessaging.handlers import ChatRoomBase, DBUtils
from MaKaC.services.interface.rpc.common import ServiceError, NoReportError
from MaKaC.plugins.base import PluginFieldsHelper
from MaKaC.common.logger import Logger
import zope.interface
from bdb import Breakpoint


class ChatSMContributor(Component):

    zope.interface.implements(IContributor, INavigationContributor)

    """ChatSideMenuContributor. Fills the side menu of the conference's management menu when
    the chat plugin is active"""

    @classmethod
    def fillManagementSideMenu(cls, obj, params={}):
        params['Instant Messaging'] = wcomponents.SideMenuItem(_("Instant Messaging"), urlHandlers.UHConfModifChat.getURL( obj._conf ))

    @classmethod
    def getActiveNavigationItem(cls, obj, params={}):
        pass

    @classmethod
    def confDisplaySMFillDict(self, obj, params):
        componentsDict = params['dict']
        conf = params['conf']

        componentsDict["instantMessaging"] =  { \
                "caption": _("Instant Messaging"), \
                "URL": str(urlHandlers.UHConferenceInstantMessaging.getURL(conf)), \
                "staticURL": "", \
                "parent": ""}

    @classmethod
    def confDisplaySMFillOrderedKeys(self, obj, list):
        list.append("instantMessaging")


    @classmethod
    def confDisplaySMShow(self, obj, params):
        obj._instantMessaging = obj._sectionMenu.getLinkByName("instantMessaging")
        if not DBUtils.roomsToShow(obj._conf):
            obj._instantMessaging.setVisible(False)


    @classmethod
    def meetingAndLectureDisplay(self, obj, params):
        out = params['out']
        conf = params['conf']
        if DBUtils.roomsToShow(conf):
            out.openTag("chatrooms")
            for chatroom in DBUtils.getShowableRooms(conf):
                out.openTag("chatroom")

                out.writeTag("id", chatroom.getId())
                out.writeTag("name", chatroom.getTitle())
                out.writeTag("server", 'conference.' + chatroom.getHost() if chatroom.getCreateRoom() else chatroom.getHost())
                out.writeTag("description", chatroom.getDescription())
                out.writeTag("reqPassword", _('Yes') if len(chatroom.getPassword()) > 0 else _('No'))
                out.writeTag("showPassword", chatroom.getShowPass())
                out.writeTag("password", chatroom.getPassword())
                out.writeTag("createRoom", chatroom.getCreateRoom())

                out.closeTag("chatroom")
            out.closeTag("chatrooms")


class ChatroomStorage(Component):
    zope.interface.implements(IListener, IInstantMessagingListener)

    @classmethod
    def createChatroom(cls, obj, chatroom):
        """ Inserts the object in the database according to all the kind of indexing types, in this case:
        -Chat rooms by conference
        -Chat rooms by user
        -Chat rooms by name (to check if there's already a chat room with that name in our Jabber server)
        -Chat rooms by ID (to access faster to the object when querying)
        """
        root = DBUtils.getChatRoot()
        room, conference = chatroom, chatroom.getConference()

        if not root.has_key('counter'):
            root['counter'] = Counter()

        # index by conference id
        if not root.has_key('indexByConf'):
            root['indexByConf'] = OOBTree()
        confRooms = root['indexByConf']
        if not confRooms.has_key(conference.getId()):
            confRooms[conference.getId()] = OOTreeSet()

        room.setId(DBUtils.newID(room.getConference()))
        # Index by chat room's name
        if not root.has_key('indexByCRName'):
             root['indexByCRName'] = OOBTree()
        roomsName = root['indexByCRName']
        roomRepeated = False
        roomNameExists = roomsName.has_key(room.getTitle())
        if roomNameExists:
            for cr in roomsName[room.getTitle()]:
                #if there is a chat room repeated in the server (either ours or an external one) we have a problem
                if cr.getTitle() == room.getTitle() and cr.getHost() == room.getHost():
                    roomRepeated = True

        if roomRepeated:
            raise NoReportError( _('There is already a chat room in that server with that name, please choose another one'))
        elif not roomNameExists:
            roomsName[room.getTitle()] = OOTreeSet()

        # Index by id
        if not root.has_key('indexByID'):
             root['indexByID'] = OOBTree()
        roomsID = root['indexByID']
        if roomsID.has_key(room.getId()):
            raise ServiceError( message=_('There is already a chat room with the same id'))

        # Index by room creator
        if not root.has_key('indexByUser'):
             root['indexByUser'] = OOBTree()
        roomsUser = root['indexByUser']
        if not roomsUser.has_key(room.getOwner().getId()):
            roomsUser[room.getOwner().getId()] = OOTreeSet()

        #there were no exceptions, we can insert the room in the db
        roomsName[room.getTitle()].insert(room)
        confRooms[conference.getId()].insert(room)
        roomsID[room.getId()] = room
        roomsUser[room.getOwner().getId()].insert(room)


    @classmethod
    def editChatroom(self, obj, params):
        oldTitle = params['oldTitle']
        newRoom = params['newRoom']
        #we have an index by the chat room name. If, while editing, someone changes the chat room name, we'll have to update the index
        if oldTitle != newRoom.getTitle():
            #the title has been changed. Get rid of the old index and substitute it for the new one
            root = DBUtils.getChatRoot()
            root['indexByCRName'][oldTitle].remove(newRoom)
            #if there are no more rooms with the same name, we don't want the index
            if len( root['indexByCRName'][oldTitle] ) is 0:
                root['indexByCRName'].pop(oldTitle)
            if not root['indexByCRName'].has_key(newRoom.getTitle()):
                root['indexByCRName'][newRoom.getTitle()] = OOTreeSet()
            root['indexByCRName'][newRoom.getTitle()].insert(newRoom)


    @classmethod
    def deleteChatroom(cls, obj, chatroom):
        """ Deletes the chat room in the database according to all kind of indexing types"""
        root = DBUtils.getChatRoot()#pfh.getStorage()
        try:
            confId = obj._conferenceID
            #if we have the same room used in two or more different conferences, we just delete it from the
            #conferences list in the chat room and from the IndexByConf index
            if len(chatroom.getConferences()) > 1:
                chatroom.getConferences().pop(confId)
                root['indexByConf'][confId].remove(chatroom)
                if len( root['indexByConf'][confId] ) is 0:
                    root['indexByConf'].pop(confId)

            else:
            #there's only 1 conference using the chat room
                root['indexByConf'][confId].remove(chatroom)
                #if there are no more rooms in the conference, we don't want the index
                if len( root['indexByConf'][confId] ) is 0:
                    root['indexByConf'].pop(confId)

                title = chatroom.getTitle()
                root['indexByCRName'][title].remove(chatroom)
                #if there are no more rooms with the same name, we don't want the index
                if len( root['indexByCRName'][title] ) is 0:
                    root['indexByCRName'].pop(title)

                root['indexByID'].pop(chatroom.getId())

                user = chatroom.getOwner().getId()
                root['indexByUser'][user].remove(chatroom)
                #if there are no more rooms created by that user, we don't want the index
                if len( root['indexByUser'][user] ) is 0:
                    root['indexByUser'].pop(user)

        except Exception, e:
            raise ServiceError(message=str(e))


    @classmethod
    def addConference2Room(self, obj, room):
        root = DBUtils.getChatRoot()
        confId = obj._conference#
        try:
            #someone deleted ALL the chat rooms while the pop up was open
            if not root.has_key('indexByConf'):
                root['indexByConf'] = OOBTree()
            confRooms = root['indexByConf']
            #there are no chat rooms for this conference
            if not confRooms.has_key(confId):
                confRooms[confId] = OOTreeSet()
            confRooms[confId].insert(room)

        except Exception, e:
            raise NoReportError( _('The chat room %s could not be re-used' %room.getTitle()))

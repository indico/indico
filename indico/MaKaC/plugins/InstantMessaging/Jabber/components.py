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
from MaKaC.conference import ConferenceHolder
from MaKaC.common.Counter import Counter
from MaKaC.webinterface import wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.plugins.helpers import *
from MaKaC.services.interface.rpc.common import ServiceError, NoReportError
from MaKaC.common.mail import GenericMailer
from MaKaC.webinterface.mail import GenericNotification
from MaKaC.common.info import HelperMaKaCInfo
import zope.interface


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
        sideMenuItemsDict = params['dict']
        conf = params['conf']

        sideMenuItemsDict["instantMessaging"] =  { \
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
        if not DBHelpers.roomsToShow(obj._conf):
            obj._instantMessaging.setVisible(False)


    @classmethod
    def meetingAndLectureDisplay(self, obj, params):
        out = params['out']
        conf = params['conf']
        if DBHelpers.roomsToShow(conf):
            out.openTag("chatrooms")
            for chatroom in DBHelpers.getShowableRooms(conf):
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

    def __init__(self):
        #it's the first thing to do when having these events
        self.priority=1

    @classmethod
    def createChatroom(cls, obj, room):
        """ Inserts the object in the database according to all the kind of indexing types, in this case:
        -Chat rooms by conference
        -Chat rooms by user
        -Chat rooms by name (to check if there's already a chat room with that name in our Jabber server)
        -Chat rooms by ID (to access faster to the object when querying)
        """
        conference = room.getConference()
        CounterIndexHelper()

        # index by conference id
        confIndex = IndexByConfHelper(conference.getId())
        room.setId(DBHelpers.newID(room.getConference()))
        confIndex.add(room)

        # Index by chat room's name
        crNameIndex = IndexByCRNameHelper(room.getTitle())
        crNameIndex.add(room)

        # Index by id
        idIndex = IndexByIDHelper()
        idIndex.add(room)

        # Index by room creator
        userIndex = IndexByUserHelper(room.getOwner().getId())
        userIndex.add(room)

    @classmethod
    def editChatroom(self, obj, params):
        oldTitle = params['oldTitle']
        newRoom = params['newRoom']
        #we have an index by the chat room name. If, while editing, someone changes the chat room name, we'll have to update the index
        if oldTitle != newRoom.getTitle():
            #the title has been changed. Get rid of the old index and substitute it for the new one
            crNameIndex = IndexByCRNameHelper(newRoom.getTitle())
            crNameIndex.delete(newRoom, oldTitle)
            crNameIndex.add(newRoom)

    @classmethod
    def deleteChatroom(cls, obj, chatroom):
        """ Deletes the chat room in the database according to all kind of indexing types"""
        try:
            confId = obj._conferenceID
            #if we have the same room used in two or more different conferences, we just delete it from the
            #conferences list in the chat room and from the IndexByConf index
            chatroom.getConferences().pop(confId)
            confIndex = IndexByConfHelper(confId)
            confIndex.delete(chatroom)

            if len(chatroom.getConferences()) is 0:
                #there are no more references to the chat room, we completely delete it
                crNameIndex = IndexByCRNameHelper(chatroom.getTitle())
                crNameIndex.delete(chatroom)

                idIndex = IndexByIDHelper()
                idIndex.delete(chatroom)

                userIndex = IndexByUserHelper(chatroom.getOwner().getId())
                userIndex.delete(chatroom)

        except Exception, e:
            raise ServiceError(message=str(e))

    @classmethod
    def addConference2Room(self, obj, room):
        """ When we re use a chat room for another conference(s), this is the method called"""
        confId = obj._conference#
        try:
            confIndex = IndexByConfHelper(confId)
            confIndex.add(room)

        except Exception, e:
            raise NoReportError( _('The chat room %s could not be re-used' %room.getTitle()))


class ChatroomMailer(Component):
    """ Sends emails to the administrators when a chat room related event happens"""

    zope.interface.implements(IListener, IInstantMessagingListener)

    @classmethod
    def createChatroom(cls, obj, room):
        pf = PluginFieldsHelper('InstantMessaging', 'Jabber')
        userList = pf.getOption('additionalEmails')
        if pf.getOption('sendMailNotifications'):
            userList.extend( [user.getEmail() for user in pf.getOption('admins')] )

        cn = ChatroomsNotification(room, userList)
        GenericMailer.sendAndLog(cn.create(room), room.getConference(), "MaKaC/plugins/InstantMessaging/Jabber/components.py", room.getOwner())

    @classmethod
    def editChatroom(self, obj, params):
        room = params['newRoom']
        pf = PluginFieldsHelper('InstantMessaging', 'Jabber')
        userList = pf.getOption('additionalEmails')
        if pf.getOption('sendMailNotifications'):
            userList.extend( [user.getEmail() for user in pf.getOption('admins')] )

        cn = ChatroomsNotification(room, userList)
        GenericMailer.sendAndLog(cn.edit(room, ConferenceHolder().getById(obj._conferenceID)), \
                                 ConferenceHolder().getById(obj._conferenceID), \
                                 "MaKaC/plugins/InstantMessaging/Jabber/components.py", \
                                 room.getOwner())


    @classmethod
    def deleteChatroom(cls, obj, room):
        pf = PluginFieldsHelper('InstantMessaging', 'Jabber')
        userList = pf.getOption('additionalEmails')
        if pf.getOption('sendMailNotifications'):
            userList.extend( [user.getEmail() for user in pf.getOption('admins')] )

        cn = ChatroomsNotification(room, userList)
        GenericMailer.sendAndLog(cn.delete(room, ConferenceHolder().getById(obj._conferenceID)),\
                                 ConferenceHolder().getById(obj._conferenceID), \
                                 "MaKaC/plugins/InstantMessaging/Jabber/components.py", \
                                 room.getOwner())

    @classmethod
    def addConference2Room(self, obj, room):
        confId = obj._conference
        pf = PluginFieldsHelper('InstantMessaging', 'Jabber')
        userList = pf.getOption('additionalEmails')
        if pf.getOption('sendMailNotifications'):
            userList.extend( [user.getEmail() for user in pf.getOption('admins')] )

        cn = ChatroomsNotification(room, userList)
        GenericMailer.sendAndLog(cn.create(room, ConferenceHolder().getById(obj._conference)), \
                                           ConferenceHolder().getById(obj._conference), \
                                           "MaKaC/plugins/InstantMessaging/Jabber/components.py", \
                                           room.getOwner())


class ChatroomsNotification(GenericNotification):
    """ Template to build an email notification for a given chat room. """

    def __init__(self, room, userList):
        GenericNotification.__init__(self)
        self.setFromAddr("Indico Mailer<%s>"%HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail())
        self.setToList(userList)

    def create(self, room, conference=None):
        if conference is None:
            conference = room.getConference()
        self.setSubject('[Indico] Chat room succesfully created')
        self.setBody("""    Dear Indico user,
The chat room with name %s has been successfully created in the conference %s (id: %s)
by the user %s.

Thank you for using our system.""" %(room.getTitle(), conference.getTitle(), conference.getId(), room.getOwner().getFullName()))
        return self

    def edit(self, room, conference):
        conference = room.getConference()
        self.setSubject("""[Indico] Chat room succesfully edited""")
        self.setBody("""    Dear Indico user,
The chat room with name %s has been successfully edited in the conference %s (id: %s)
by the user %s.

Thank you for using our system.""" %(room.getTitle(), conference.getTitle(), conference.getId(), room.getOwner().getFullName()))
        return self

    def delete(self, room, conference):
        conference = room.getConference()
        self.setSubject("""[Indico] Chat room succesfully deleted""")
        self.setBody("""    Dear Indico user,
The chat room with name %s has been successfully deleted from the conference %s (id: %s)
by the user %s.

Thank you for using our system.""" %(room.getTitle(), conference.getTitle(), conference.getId(), room.getOwner().getFullName()))
        return self


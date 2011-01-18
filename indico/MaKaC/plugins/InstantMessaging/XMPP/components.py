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

from MaKaC.plugins.InstantMessaging.notificationComponents import IInstantMessagingListener
from MaKaC.plugins.base import Observable, PluginsHolder
from MaKaC.plugins.util import PluginsWrapper, PluginFieldsWrapper
from MaKaC.plugins.helpers import DBHelpers, MailHelper, GeneralLinkGenerator
from MaKaC.plugins.InstantMessaging.indexes import IndexByConf, IndexByCRName, IndexByID, IndexByUser
from MaKaC.i18n import _
from MaKaC.conference import ConferenceHolder
from MaKaC.common.contextManager import ContextManager
from MaKaC.common.externalOperationsManager import ExternalOperationsManager
from MaKaC.common.mail import GenericMailer
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.webinterface import wcomponents
from MaKaC.webinterface.mail import GenericNotification
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.services.interface.rpc.common import ServiceError, NoReportError
import zope.interface

from indico.core.api import Component
from indico.core.api.conference import INavigationContributor


class ChatSMContributor(Component, Observable):

    zope.interface.implements(INavigationContributor)

    """ChatSideMenuContributor. Fills the side menu of the conference's management menu when
    the chat plugin is active"""

    @classmethod
    def fillManagementSideMenu(cls, obj, params={}):
        params['Instant Messaging'] = wcomponents.SideMenuItem(_("Chat Rooms"), urlHandlers.UHConfModifChat.getURL( obj._conf ))

    @classmethod
    def getActiveNavigationItem(cls, obj, params={}):
        pass

    @classmethod
    def confDisplaySMFillDict(cls, obj, params):
        sideMenuItemsDict = params['dict']
        conf = params['conf']

        sideMenuItemsDict["instantMessaging"] =  { \
                "caption": _("Chat Rooms"), \
                "URL": str(urlHandlers.UHConferenceInstantMessaging.getURL(conf)), \
                "staticURL": "", \
                "parent": ""}

    @classmethod
    def confDisplaySMFillOrderedKeys(cls, obj, list):
        list.append("instantMessaging")


    @classmethod
    def confDisplaySMShow(cls, obj, params):
        obj._instantMessaging = obj._sectionMenu.getLinkByName("instantMessaging")
        if not DBHelpers.roomsToShow(obj._conf):
            obj._instantMessaging.setVisible(False)


    @classmethod
    def meetingAndLectureDisplay(cls, obj, params):
        out = params['out']
        conf = params['conf']
        if DBHelpers.roomsToShow(conf):
            linksList = PluginsHolder().getPluginType('InstantMessaging').getOption('customLinks').getValue()
            out.openTag("chatrooms")
            for chatroom in DBHelpers.getShowableRooms(conf):
                out.openTag("chatroom")

                out.writeTag("id", chatroom.getId())
                out.writeTag("name", chatroom.getTitle())
                out.writeTag("server", 'conference.' + chatroom.getHost() if chatroom.getCreatedInLocalServer() else chatroom.getHost())
                out.writeTag("description", chatroom.getDescription())
                out.writeTag("reqPassword", _('Yes') if len(chatroom.getPassword()) > 0 else _('No'))
                out.writeTag("showPassword", chatroom.getShowPass())
                out.writeTag("password", chatroom.getPassword())
                out.writeTag("createdInLocalServer", chatroom.getCreatedInLocalServer())
                out.openTag("links")
                if linksList.__len__() > 0:
                    out.writeTag("linksToShow", 'true')
                else:
                    out.writeTag("linksToShow", 'false')

                for link in linksList:
                    out.openTag("customLink")
                    out.writeTag("name", link['name'])
                    out.writeTag("structure", GeneralLinkGenerator(chatroom, link['structure']).generate())
                    out.closeTag("customLink")

                out.closeTag("links")
                out.closeTag("chatroom")
            out.closeTag("chatrooms")

            out.writeTag("how2connect", PluginFieldsWrapper('InstantMessaging', 'XMPP').getOption('ckEditor'))

    @classmethod
    def addCheckBox2CloneConf(cls, obj, list):
        """ we show the clone checkbox if:
            * The XMPP Plugin is active.
            * There are rooms in the event created by the user who wants to clone
        """
        #list of creators of the chat rooms
        ownersList = [cr.getOwner() for cr in DBHelpers().getChatroomList(obj._conf)]
        if PluginsWrapper('InstantMessaging', 'XMPP').isActive() and obj._rh._aw._currentUser in ownersList:
            list['cloneOptions'] += _("""<li><input type="checkbox" name="cloneChatrooms" id="cloneChatrooms" value="1" />_("Chat Rooms")</li>""")

    @classmethod
    def fillCloneDict(self, obj, params):
        options = params['options']
        paramNames = params['paramNames']
        options['chatrooms'] = 'cloneChatrooms' in paramNames

    @classmethod
    def cloneEvent(cls, confToClone, params):
        """ we'll clone only the chat rooms created by the user who is cloning the conference """
        conf = params['conf']
        user = params['user']
        options = params['options']
        ContextManager.getdefault('mailHelper', MailHelper())

        if options.get("chatrooms", True):
            crList = DBHelpers().getChatroomList(confToClone)
            ownersList = [cr.getOwner() for cr in crList]
            if PluginsWrapper('InstantMessaging', 'XMPP').isActive():
                 for cr in crList:
                     if user is cr.getOwner():
                         cls()._notify('addConference2Room', {'room':cr, 'conf':conf.getId()})

        ContextManager.get('mailHelper').sendMails()


class ChatroomStorage(Component):
    zope.interface.implements(IInstantMessagingListener)

    def __init__(self):
        #it's the first thing to do when having these events
        self.priority=1

    @classmethod
    def createChatroom(cls, obj, params):
        """ Inserts the object in the database according to all the kind of indexing types, in this case:
        -Chat rooms by conference
        -Chat rooms by user
        -Chat rooms by name (to check if there's already a chat room with that name in our XMPP server)
        -Chat rooms by ID (to access faster to the object when querying)
        """
        room = params['room']

        conference = room.getConference()

        # index by conference id
        confIndex = IndexByConf(conference.getId())
        room.setId(DBHelpers.newID())
        confIndex.index(room)

        # Index by chat room's name
        crNameIndex = IndexByCRName(room.getTitle())
        crNameIndex.index(room)

        # Index by id
        idIndex = IndexByID()
        idIndex.index(room)

        # Index by room creator
        userIndex = IndexByUser(room.getOwner().getId())
        userIndex.index(room)

    @classmethod
    def editChatroom(self, obj, params):
        oldTitle = params['oldTitle']
        newRoom = params['newRoom']
        #we have an index by the chat room name. If, while editing, someone changes the chat room name, we'll have to update the index
        if oldTitle != newRoom.getTitle():
            #the title has been changed. Get rid of the old index and substitute it for the new one
            crNameIndex = IndexByCRName(newRoom.getTitle())
            crNameIndex.unindex(newRoom, oldTitle)
            crNameIndex.index(newRoom)

    @classmethod
    def deleteChatroom(cls, obj, params):
        """ Deletes the chat room in the database according to all kind of indexing types"""
        try:
            chatroom = params['room']

            confId = obj._conferenceID
            #if we have the same room used in two or more different conferences, we just delete it from the
            #conferences list in the chat room and from the IndexByConf index
            chatroom.getConferences().pop(confId)
            confIndex = IndexByConf(confId)
            confIndex.unindex(chatroom)

            if len(chatroom.getConferences()) is 0:
                #there are no more references to the chat room, we completely delete it
                crNameIndex = IndexByCRName(chatroom.getTitle())
                crNameIndex.unindex(chatroom)

                idIndex = IndexByID()
                idIndex.unindex(chatroom)

                userIndex = IndexByUser(chatroom.getOwner().getId())
                userIndex.unindex(chatroom)

        except Exception, e:
            raise ServiceError(message=str(e))

    @classmethod
    def addConference2Room(cls, obj, params):
        """ When we re use a chat room for another conference(s), this is the method called.
            It may be called from the AJAX service, but also from the clone event. Since we
            don't know it, we have to check the parameters accordingly"""
        room = params['room']
        confId = params['conf']

        try:
            confIndex = IndexByConf(confId)
            confIndex.index(room)

        except Exception, e:
            raise NoReportError( _('The chat room %s could not be re-used' %room.getTitle()))


class ChatroomMailer(Component):
    """ Sends emails to the administrators when a chat room related event happens"""

    zope.interface.implements(IInstantMessagingListener)

    @classmethod
    def createChatroom(cls, obj, params):
        room = params['room']
        # we give this operation the name createSomething in the externaloperationsmanager
        # we will execute the method performOperation in a chat room creation, which will send an email to all the requested users
        # saying that a chat room was created. We pass the 2 mandatory arguments and finally the arguments required for performOperation
        # (in this case, only one argument)
        ExternalOperationsManager.execute(cls, "create_"+str(cls.__class__)+str(room.getId()), cls.performOperation, 'create', room.getConference(), room, room)

    @classmethod
    def editChatroom(cls, obj, params):
        room = params['newRoom']
        conf = ConferenceHolder().getById(obj._conferenceID)
        ExternalOperationsManager.execute(cls, "edit_"+str(cls.__class__)+str(room.getId()), cls.performOperation, 'edit', conf, room, room, conf)

    @classmethod
    def deleteChatroom(cls, obj, params):
        room = params['room']
        conf = ConferenceHolder().getById(obj._conferenceID)
        ExternalOperationsManager.execute(cls, "delete_"+str(cls.__class__)+str(room.getId()), cls.performOperation, 'delete', conf, room, room, conf)

    @classmethod
    def addConference2Room(cls, obj, params):
        room = params['room']
        conf = ConferenceHolder().getById(params['conf'])
        #without the number added it would only send 1 mail, because for every new chat room it'd think that there has been a retry
        ExternalOperationsManager.execute(cls, "add_"+str(cls.__class__)+str(room.getId()), cls.performOperation, 'create', conf, room, room, conf)

    @classmethod
    def performOperation(cls, operation, conf, room, *args):
        """ The 4 operations of this class are quite the same, so we pass the name of the operation, the conference they belong to,
            the chat room for which we are creating the operation and, finally, a list of the arguments needed for the operation"""

        # get the list of users that will receive emails
        pf = PluginFieldsWrapper('InstantMessaging', 'XMPP')
        userList = list(pf.getOption('additionalEmails'))
        if pf.getOption('sendMailNotifications'):
            userList.extend( [user.getEmail() for user in pf.getOption('admins')] )
        if not len(userList) is 0:
            try:
                cn = ChatroomsNotification(room, userList)
                ContextManager.get('mailHelper').newMail(GenericMailer.sendAndLog, getattr(cn, operation)(*args), \
                                         conf, \
                                         "MaKaC/plugins/InstantMessaging/XMPP/components.py", \
                                         room.getOwner())
            except Exception, e:
                raise ServiceError(message=_('There was an error while contacting the mail server. No notifications were sent: %s'%e))


class ChatroomsNotification(GenericNotification):
    """ Template to build an email notification for a given chat room. """

    def __init__(self, room, userList):
        GenericNotification.__init__(self)
        self.setFromAddr("Indico Mailer<%s>"%HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail())
        self.setToList(userList)

    def create(self, room, conference=None):
        """ If conference is None it means we're creating the chat room for the first time
        if not it means we're re-using an existing chat room """
        if conference is None:
            conference = room.getConference()
        self.setSubject('[Indico] Chat room succesfully created')
        self.setBody("""    Dear Indico user,
The chat room with name %s has been successfully created in the conference %s (id: %s)
by the user %s.

Thank you for using our system.""" %(room.getTitle(), conference.getTitle(), conference.getId(), room.getOwner().getFullName()))
        return self

    def edit(self, room, conference):
        self.setSubject("""[Indico] Chat room succesfully edited""")
        self.setBody("""    Dear Indico user,
The chat room with name %s has been successfully edited in the conference %s (id: %s)
by the user %s.

Thank you for using our system.""" %(room.getTitle(), conference.getTitle(), conference.getId(), room.getOwner().getFullName()))
        return self

    def delete(self, room, conference):
        self.setSubject("""[Indico] Chat room succesfully deleted""")
        self.setBody("""    Dear Indico user,
The chat room with name %s has been successfully deleted from the conference %s (id: %s)
by the user %s.

Thank you for using our system.""" %(room.getTitle(), conference.getTitle(), conference.getId(), room.getOwner().getFullName()))
        return self

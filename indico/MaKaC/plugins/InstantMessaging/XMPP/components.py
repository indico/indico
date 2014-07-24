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

from MaKaC.plugins.InstantMessaging.notificationComponents import IInstantMessagingListener
from MaKaC.plugins.base import Observable, PluginsHolder
from MaKaC.plugins.util import PluginsWrapper, PluginFieldsWrapper
from MaKaC.plugins.InstantMessaging.XMPP.helpers import GeneralLinkGenerator
from MaKaC.plugins.helpers import DBHelpers
from MaKaC.plugins.InstantMessaging.indexes import IndexByConf, IndexByCRName, IndexByID, IndexByUser
from MaKaC.plugins.InstantMessaging import urlHandlers
from MaKaC.plugins.InstantMessaging.pages import WPluginHelp
from MaKaC.i18n import _
from MaKaC.plugins import InstantMessaging
from indico.util.i18n import i18nformat, i18nformat, N_
from MaKaC.conference import ConferenceHolder
from MaKaC.common.externalOperationsManager import ExternalOperationsManager
from MaKaC.common.mail import GenericMailer
from MaKaC.webinterface import wcomponents
from MaKaC.webinterface.mail import GenericNotification
from MaKaC.services.interface.rpc.common import ServiceError
import zope.interface

from indico.core.extpoint import Component
from indico.core.extpoint.events import INavigationContributor
from indico.core.extpoint.plugins import IPluginDocumentationContributor
from indico.core.config import Config


class ChatSMContributor(Component, Observable):

    zope.interface.implements(INavigationContributor)

    """ChatSideMenuContributor. Fills the side menu of the conference's management menu when
    the chat plugin is active"""

    @classmethod
    def fillManagementSideMenu(cls, obj, params={}):
        instantMessagingAdmins = []
        for imPlugin in PluginsHolder().getPluginType('InstantMessaging').getPluginList():
            instantMessagingAdmins.extend(imPlugin.getOption("admins").getValue())
        if obj._conf.canModify(obj._rh._aw) or  obj._rh._aw.getUser() in instantMessagingAdmins:
            params['Instant Messaging'] = wcomponents.SideMenuItem(_("Chat Rooms"),
                                                               urlHandlers.UHConfModifChat.getURL( obj._conf ))

    @classmethod
    def getActiveNavigationItem(cls, obj, params={}):
        pass

    @classmethod
    def confDisplaySMFillDict(cls, obj, params):
        sideMenuItemsDict = params['dict']
        conf = params['conf']

        sideMenuItemsDict["instantMessaging"] =  { \
                "caption": N_("Chat Rooms"), \
                "URL": urlHandlers.UHConferenceInstantMessaging, \
                "staticURL": "", \
                "parent": ""}

    @classmethod
    def confDisplaySMFillOrderedKeys(cls, obj, list):
        list.append("instantMessaging")


    @classmethod
    def confDisplaySMShow(cls, obj, params):
        obj._instantMessaging = obj._sectionMenu.getLinkByName("instantMessaging")
        if obj._instantMessaging and not DBHelpers.roomsToShow(obj._conf):
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
                out.writeTag("reqPassword", _('Yes') if chatroom.getPassword() else _('No'))
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
        if PluginsWrapper('InstantMessaging', 'XMPP').isActive():
            list['cloneOptions'] += '<li><input type="checkbox" name="cloneChatrooms"' \
                ' id="cloneChatrooms" value="1" />{0}</li>'.format(_("Chat Rooms"))

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

        if options.get("chatrooms", True):
            crList = DBHelpers().getChatroomList(confToClone)
            ownersList = [cr.getOwner() for cr in crList]
            if PluginsWrapper('InstantMessaging', 'XMPP').isActive():
                for cr in crList:
                    if user is cr.getOwner():
                        cls()._notify('addConference2Room', {'room':cr, 'conf':conf.getId(), 'clone': True})


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

        conference = params['conference']

        # index by conference id
        confIndex = IndexByConf()
        room.setId(DBHelpers.newID())
        confIndex.index(conference.getId(), room)

        # Index by chat room's name
        crNameIndex = IndexByCRName()
        crNameIndex.index(room)

        # Index by id
        idIndex = IndexByID()
        idIndex.index(room)

        # Index by room creator
        userIndex = IndexByUser()
        userIndex.index(room.getOwner().getId(), room)

    @classmethod
    def editChatroom(self, obj, params):
        oldTitle = params['oldTitle']
        newRoom = params['newRoom']
        userId = params['userId']

        #we have an index by the chat room name. If, while editing, someone changes the chat room name, we'll have to update the index
        if oldTitle != newRoom.getTitle():
            #the title has been changed. Get rid of the old index and substitute it for the new one
            crNameIndex = IndexByCRName()
            crNameIndex.unindex(newRoom, oldTitle)
            crNameIndex.index(newRoom)

            # For dynamic loading this needs to be in alphabetical order,
            # therefore reindex on change.
            userIndex = IndexByUser()
            userIndex.reindex(userId, newRoom, oldTitle)

    @classmethod
    def deleteChatroom(cls, obj, params):
        """ Deletes the chat room in the database according to all kind of indexing types"""

        chatroom = params['room']

        confId = obj._conferenceID
        #if we have the same room used in two or more different conferences, we just delete it from the
        #conferences list in the chat room and from the IndexByConf index
        chatroom.getConferences().pop(confId)
        confIndex = IndexByConf()
        confIndex.unindex(confId, chatroom)

        if len(chatroom.getConferences()) is 0:
            #there are no more references to the chat room, we completely delete it
            crNameIndex = IndexByCRName()
            crNameIndex.unindex(chatroom)

            idIndex = IndexByID()
            idIndex.unindex(chatroom)

            userIndex = IndexByUser()
            userIndex.unindex(chatroom.getOwner().getId(), chatroom)

    @classmethod
    def addConference2Room(cls, obj, params):
        """ When we re use a chat room for another conference(s), this is the method called.
            It may be called from the AJAX service, but also from the clone event. Since we
            don't know it, we have to check the parameters accordingly"""
        room = params['room']
        confId = params['conf']
        room.setConference(ConferenceHolder().getById(confId))
        confIndex = IndexByConf()
        confIndex.index(confId, room)


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
        ExternalOperationsManager.execute(cls, "create_"+str(cls.__class__)+str(room.getId()), cls.performOperation, 'create', room.getConferences().values()[0], room, room)

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
        if not params.get("clone", False):
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
                GenericMailer.sendAndLog(getattr(cn, operation)(*args), conf,
                                         PluginsHolder().getPluginType('InstantMessaging').getPlugin("XMPP").getName())
            except Exception, e:
                raise ServiceError(message=_('There was an error while contacting the mail server. No notifications were sent: %s'%e))


class ChatroomsNotification(GenericNotification):
    """ Template to build an email notification for a given chat room. """

    def __init__(self, room, userList):
        GenericNotification.__init__(self)
        self.setFromAddr("Indico Mailer <%s>"%Config.getInstance().getSupportEmail())
        self.setToList(userList)

    def create(self, room, conference=None):
        """ If conference is None it means we're creating the chat room for the first time
        if not it means we're re-using an existing chat room """
        if conference is None:
            conference = room.getConferences().values()[0]
        self.setSubject("[Indico] [IM] Chat room created in conference %s: %s" % (conference.getId(), room.getTitle()))
        self.setBody("""    Dear Indico user,
The chat room with name %s has been successfully created in the conference %s (id: %s)
by the user %s.

Thank you for using our system.""" %(room.getTitle(), conference.getTitle(), conference.getId(), room.getOwner().getFullName()))
        return self

    def edit(self, room, conference):
        self.setSubject("[Indico] [IM] Chat room edited in conference %s: %s" % (conference.getId(), room.getTitle()))
        self.setBody("""    Dear Indico user,
The chat room with name %s has been successfully edited in the conference %s (id: %s)
by the user %s.

Thank you for using our system.""" %(room.getTitle(), conference.getTitle(), conference.getId(), room.getOwner().getFullName()))
        return self

    def delete(self, room, conference):
        self.setSubject("[Indico] [IM] Chat room deleted in conference %s: %s" % (conference.getId(), room.getTitle()))
        self.setBody("""    Dear Indico user,
The chat room with name %s has been successfully deleted from the conference %s (id: %s)
by the user %s.

Thank you for using our system.""" %(room.getTitle(), conference.getTitle(), conference.getId(), room.getOwner().getFullName()))
        return self


class PluginDocumentationContributor(Component):

    zope.interface.implements(IPluginDocumentationContributor)

    def providePluginDocumentation(self, obj):
        return WPluginHelp.forModule(InstantMessaging).getHTML({})

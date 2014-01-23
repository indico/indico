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

import urllib2, os, tempfile, stat
from MaKaC.plugins.InstantMessaging.XMPP.chatroom import XMPPChatroom
from MaKaC.plugins.InstantMessaging.handlers import ChatroomServiceBase
from MaKaC.services.implementation.base import ServiceBase, ParameterManager
from MaKaC.services.interface.rpc.common import ServiceError, NoReportError
from MaKaC.common import log
from indico.core.config import Config
from MaKaC.common.contextManager import ContextManager
from MaKaC.common.logger import Logger
from MaKaC.common.externalOperationsManager import ExternalOperationsManager
from MaKaC.common.timezoneUtils import nowutc, DisplayTZ
from MaKaC.common.fossilize import fossilize
from MaKaC.plugins import Observable
from MaKaC.plugins.util import PluginFieldsWrapper
from MaKaC.plugins.helpers import DBHelpers
from MaKaC.plugins.InstantMessaging.XMPP.helpers import DeleteLogLinkGenerator, LogLinkGenerator, generateCustomLinks, generateLogLink, XMPPLogsActivated
from MaKaC.i18n import _

from MaKaC.plugins.InstantMessaging.XMPP.bot import IndicoXMPPBotRoomExists, IndicoXMPPBotCreateRoom, IndicoXMPPBotEditRoom, IndicoXMPPBotDeleteRoom, IndicoXMPPBotGetPreferences
from MaKaC.conference import ConferenceHolder, LocalFile


class XMPPChatroomService( ChatroomServiceBase ):

    messages = { 'default': _('There was an error while connecting to the XMPP server'),\
                 'sameId': _('There is already a chat room with the same id'), \
                 'sameName': _('There is already a chat room in the server with that name, please choose another one'), \
                 'creating': _('There was an error while creating the chat room in the local server. Please try again later'), \
                 'editing': _('There was an error while editing the chat room in the local server. Please try again later'), \
                 'deleting': _('There was an error while deleting the chat room in the XMPP server. Please try to do it manually from your client' \
                               ' or contact the administrators'), \
                 'connecting': _('There was an error while connecting to the XMPP server. Maybe the username or password are not correct'), \
                 'CRdeletedFromClient': _('Someone deleted the chat room from the XMPP server since this page was loaded. We recommend you to delete the chatroom from Indico as well')
                 }

    def __init__(self, params):
        ChatroomServiceBase.__init__(self, params)
        #we want the data from the XMPP plugin in the InstantMessaging Plugin type
        oh = PluginFieldsWrapper('InstantMessaging', 'XMPP')
        self._botJID = oh.getOption('indicoUsername') + '@' + oh.getOption('chatServerHost')
        self._botPass = oh.getOption('indicoPassword')

    def _checkParams(self):
        ChatroomServiceBase._checkParams(self)
        pm = ParameterManager(self._params.get('chatroomParams'))

        self._description = pm.extract('description', pType=str, allowEmpty = True)
        if self._createdInLocalServer:
            oh = PluginFieldsWrapper('InstantMessaging', 'XMPP')
            self._host = oh.getOption('chatServerHost')
        else:
            self._host = pm.extract('host', pType=str, allowEmpty = False)

        self._password = pm.extract('roomPass', pType=str, allowEmpty = True, defaultValue='')
        self._showPass = pm.extract('showPass', pType=bool, allowEmpty = True)

        self._user = self._getUser()

    def processAnswer(self, answer):
        # controlled error
        if hasattr(answer, '_error') and answer._error['error']:
            # we need to make a distinction in this case to show the widget in the client
            if answer._error['reason'] is 'roomExists':
                Logger.get('InstantMessaging (XMPP-XMPP server)').error("User %s tried to create the room %s, but it exists already" % (self._room.getOwner(), self._room.getTitle()))
                raise NoReportError(self.messages['sameName'], explanation='roomExists')
            else:
                Logger.get('InstantMessaging (XMPP-XMPP server)').error("User %s executed an XMPP operation that provoked an error: %s" % (self._room.getOwner(), answer._error['reason']))
                raise ServiceError(message = answer._error['reason'])
        # this should never happen! When an error happens, it should ALWAYS be set in the
        # _error variable in bot.py
        elif not hasattr(answer, '_error'):
            Logger.get('InstantMessaging (XMPP-XMPP server)').error("Really unexpected error, no _error attribute was found. Please check this. User: %s. Chat room ID: %s" %(self._room.getOwner(), self._room.getId()))
            raise ServiceError(message = self.messages['connecting'])
        return True

    def roomExistsXMPP(self, jid, password, room):
        """ Creates the room in the XMPP server """
        try:
            self._bot = IndicoXMPPBotRoomExists(jid, password, room)
            #make operation atomic
            ExternalOperationsManager.execute(self._bot, "roomExistsXMPP", self._bot.run)
        except Exception, e:
            Logger.get('InstantMessaging (XMPP-XMPP server)').exception("Exception while checking if room existed")
            raise ServiceError(message = self.messages['default'])
        return self.processAnswer(self._bot)

    def roomPreferencesXMPP(self, jid, password, room):
        """ Creates the room in the XMPP server """
        try:
            self._bot = IndicoXMPPBotGetPreferences(self._botJID, self._botPass, self._room)
            #make operation atomic
            ExternalOperationsManager.execute(self._bot, "roomPreferencesXMPP", self._bot.run)
        except Exception, e:
            Logger.get('InstantMessaging (XMPP-XMPP server)').error("Exception while checking if room existed: %s" %e)
            raise ServiceError(message = self.messages['default'])
        return self.processAnswer(self._bot)

    def createRoomXMPP(self, jid, password, room):
        """ Creates the room in the XMPP server """
        try:
            self._bot = IndicoXMPPBotCreateRoom(jid, password, room)
            #make operation atomic
            ExternalOperationsManager.execute(self._bot, "createRoomXMPP", self._bot.run)
        except Exception, e:
            Logger.get('InstantMessaging (XMPP-XMPP server)').error("Exception while creating: %s" %e)
            raise ServiceError(message = self.messages['creating'])
        return self.processAnswer(self._bot)

    def editRoomXMPP(self, jid, password, room, checkRoomExists = True):
        """ Edits the room in the XMPP server. If checkRoomExists is set to true
            it means that we are changing the chat room name and we want to know if the new
            name is already taken in the server. If it's false it means that we only want to change
            some of the parameters in the room, so no need to check the name. """
        try:
            self._bot = IndicoXMPPBotEditRoom(jid, password, room, checkRoomExists)
            #make operation atomic
            ExternalOperationsManager.execute(self._bot, "editRoomXMPP", self._bot.run)
        except Exception, e:
            Logger.get('InstantMessaging (XMPP-XMPP server)').error("Exception while editing: %s" %e)
            raise ServiceError(message = self.messages['editing'])
        return self.processAnswer(self._bot)

    def deleteRoomXMPP(self, jid, password, room, message):
        """ Deletes the room in the XMPP server """
        try:
            self._bot = IndicoXMPPBotDeleteRoom(jid, password, room, message)
            #make operation atomic
            ExternalOperationsManager.execute(self._bot, "deleteRoomXMPP", self._bot.run)
        except Exception, e:
            Logger.get('InstantMessaging (XMPP-XMPP server)').error("Exception while deleting: %s" %e)
            raise ServiceError(message = self.messages['deleting'])
        return self.processAnswer(self._bot)

class CreateChatroom( XMPPChatroomService ):

    def _checkParams(self):
        XMPPChatroomService._checkParams(self)
        self._user = self._getUser()

    def _getAnswer( self ):
        conference = ConferenceHolder().getById(self._conferenceID)
        self._room = XMPPChatroom(self._title, \
                              self._user, \
                              conference, \
                              None, \
                              self._description, \
                              self._createdInLocalServer, \
                              self._host, \
                              self._password, \
                              self._showRoom, \
                              self._showPass)

        if self._room.getCreatedInLocalServer():
            self.roomExistsXMPP(self._botJID, self._botPass, self._room)
        try:
            self._notify('createChatroom', {'room': self._room,
                                            'conference': conference})
        except ServiceError, e:
            Logger.get('ext.im').exception("Exception while notifying observers: %s" %e)
            raise ServiceError( message=self.messages['sameId']+str(e) )
        except NoReportError, e:
            Logger.get('ext.im').error("Room exists: %s" %e)
            raise NoReportError(self.messages['sameName'], explanation='roomExists')
        except Exception, e:
            Logger.get('ext.im').error("Weird exception while notifying observers: %s" %e)
            raise ServiceError( message=str(e) )
        if self._room.getCreatedInLocalServer():
            #if we're not creating the room in our server we don't need to call the bot
            self.createRoomXMPP(self._botJID, self._botPass, self._room)

        Logger.get('ext.im').info("The room %s has been created by the user %s at %s hours" %(self._title, self._user.getName(), self._room.getModificationDate()))

        tz = DisplayTZ(self._aw, conference).getDisplayTZ()

        fossilizedRoom = self._room.fossilize(tz=tz)

        # add links to join the room
        fossilizedRoom['custom'] = generateCustomLinks(self._room)

        # add link to retrieve logs
        fossilizedRoom['logs'] = generateLogLink(self._room, conference)

        return fossilizedRoom



class EditChatroom( XMPPChatroomService ):

    def _checkParams(self):
        XMPPChatroomService._checkParams(self)

        pm = ParameterManager(self._params.get('chatroomParams'))
        self._id = pm.extract('id', pType=str, allowEmpty = False)
        self._user = self._getUser()
        self._modificationDate = nowutc()

    def _getAnswer( self ):
        values = {'title':self._title, \
                  'user':self._user, \
                  'modificationDate':self._modificationDate, \
                  'description':self._description, \
                  'createdInLocalServer':self._createdInLocalServer, \
                  'host':self._host, \
                  'password':self._password, \
                  'showRoom':self._showRoom, \
                  'showPass':self._showPass, \
                  'conference':ConferenceHolder().getById(self._conferenceID) \
                  }

        try:
            self._room = DBHelpers().getChatroom(self._id)
            oldRoom = XMPPChatroom(self._room.getTitle(), self._room.getOwner(), ConferenceHolder().getById(self._conferenceID), createdInLocalServer = self._room.getCreatedInLocalServer())
            self._room.setValues(values)

            conditions = {'titleChanged': oldRoom.getTitle() != self._room.getTitle(), \
                          'XMPPServerNotChanged': oldRoom.getCreatedInLocalServer() and self._room.getCreatedInLocalServer(), \
                          'XMPPServerChanged2External': oldRoom.getCreatedInLocalServer() and not self._room.getCreatedInLocalServer(), \
                          'XMPPServerChanged2Local': not oldRoom.getCreatedInLocalServer() and self._room.getCreatedInLocalServer() \
                         }

            if conditions['titleChanged'] and conditions['XMPPServerNotChanged'] or conditions['XMPPServerChanged2Local']:
                self.roomExistsXMPP(self._botJID, self._botPass, self._room)

            #edit the chat room in indico
            self._notify('editChatroom', {'oldTitle': oldRoom.getTitle(),
                                          'newRoom': self._room,
                                          'userId': self._user.getId()})
        except ServiceError, e:
            Logger.get('ext.im').error("Exception while editing: %s" %e)
            raise ServiceError( message=_('Problem while accessing the database: %s' %e))
        except Exception, e:
            Logger.get('ext.im').error("Weird exception while notifying observers: %s" %e)
            raise NoReportError( self.messages['editing'], explanation='roomExists')

        #edit the chat room in XMPP
        modified = False
        if conditions['titleChanged'] and conditions['XMPPServerNotChanged']:
            #before, the chat room was in the XMPP server. After editing, it is still in the XMPP server, but the title has changed.
            #This means that we'll have to delete the old room and create the new one with the new title
            message = "%s has requested to delete this room. The new chat room name is %s, please reconnect there" %(self._user.getName(), self._title)
            modified = self.deleteRoomXMPP(self._botJID, self._botPass, oldRoom, message)
            modified = self.createRoomXMPP(self._botJID, self._botPass, self._room)

        else:
            #before, the room had to be created in the XMPP server, after the modification a different server will be used
            if conditions['XMPPServerChanged2External']:
                #delete the existing room in the XMPP server
                message = "%s has requested to delete this room. The host for the new chat room is %s, please reconnect there" %(self._user.getName(), self._host)
                modified = self.deleteRoomXMPP(self._botJID, self._botPass, oldRoom, message)

            #before, the room was in an external server, now it's in the XMPP server
            elif conditions['XMPPServerChanged2Local']:
                #create the room in the XMPP server
                modified = self.createRoomXMPP(self._botJID, self._botPass, self._room)

            #no changes were made in this area, we edit the room in case it's created in the XMPP server
            elif self._room.getCreatedInLocalServer():
                modified = self.editRoomXMPP(self._botJID, self._botPass, self._room, False)

        if modified:
            Logger.get('ext.im').info("The room %s has been modified by the user %s at %s hours" %(self._title, self._user.getName(), self._room.getModificationDate()))

        return self._room.fossilizeMultiConference(values['conference'])



class DeleteChatroom( XMPPChatroomService ):

    def _checkParams(self):
        XMPPChatroomService._checkParams(self)
        pm = ParameterManager(self._params.get('chatroomParams'))
        self._id = pm.extract('id', pType=str, allowEmpty = False)
        self._room = DBHelpers().getChatroom(self._id)
        self._user = self._getUser()

    def _getAnswer( self ):
        message = _("%s has requested to delete this room. Please address this person for further information" %self._user.getName())
        #delete room from Indico
        try:
            self._notify('deleteChatroom', {'room': self._room})
        except ServiceError, e:
            Logger.get('ext.im').exception(_('Problem deleting indexes in the database for chat room %s' % self._room.getTitle()))
            raise ServiceError( message=_('Problem deleting indexes in the database for chat room %s: %s' %(self._room.getTitle(), e)))

        #delete room from our XMPP server (if neccesary)
        if self._room.getCreatedInLocalServer() and len(self._room.getConferences()) is 0:
            self.deleteRoomXMPP(self._botJID, self._botPass, self._room, message)

        # make the log folder unaccessible in the future
        if len(self._room.getConferences()) is 0:
            # we only "delete" logs when there are no conferences associated with the chat room
            url = DeleteLogLinkGenerator(self._room).generate()
            req = urllib2.Request(url, None, {'Accept-Charset' : 'utf-8'})
            document = urllib2.urlopen(req)
            Logger.get('ext.im').info("The room %s has been deleted by the user %s at %s hours" %(self._title, self._user.getName(), nowutc()))

        return True


class GetRoomPreferences( XMPPChatroomService ):

    def _checkParams(self):
        XMPPChatroomService._checkParams(self)
        pm = ParameterManager(self._params.get('chatroomParams'))
        self._id = pm.extract('id', pType=str, allowEmpty = False)
        self._user = self._getUser()

    def _getAnswer( self ):
        fieldsToCheck = {'muc#roomconfig_roomdesc': 'Description', \
                         'muc#roomconfig_roomsecret': 'Password'
                        }

        try:
            self._room = DBHelpers().getChatroom(self._id)
        except Exception, e:
            raise ServiceError( message=_('Error trying to get the chat room preferences: %s')%e)

        # this method will fill the self._bot._form attr
        self.roomPreferencesXMPP(self._botJID, self._botPass, self._room)
        #get the preferences and check updates
        for preference in self._bot._form.values['fields']:
            if preference[0] in fieldsToCheck.keys():
                #we execute setDescription or setPassword with the new value
                getattr(self._room, 'set'+ fieldsToCheck[preference[0]])(preference[1].values['value'])

        return self._room.fossilize()


class GetRoomsByUser( ServiceBase ):

    def _checkParams(self):
        self._user = self._params['usr']
        self._limit = self._params['limit']
        self._offset = self._params['offset']
        self._excl = self._params['excl'] if self._params.has_key('excl') else None

    def _getAnswer( self ):
        return fossilize(DBHelpers().getRoomsByUser(self._user, self._offset,
                                                    self._limit, self._excl))


class GetNumberOfRoomsByUser( ServiceBase ):

    def _checkParams(self):
        self._user = self._params['usr']
        self._excl = self._params['excl'] if self._params.has_key('excl') else None

    def _getAnswer(self):
        return fossilize(DBHelpers().getNumberOfRoomsByUser(self._user, self._excl))


class AddConference2Room( ServiceBase, Observable ):

    def _checkParams(self):
        self._rooms = self._params['rooms']
        self._conference = self._params['conference']

    def _getAnswer( self ):
        rooms=[]
        try:
            for roomID in self._rooms:
                try:
                    room = DBHelpers.getChatroom(roomID)
                except Exception, e:
                    Logger.get('ext.im').warning("The user %s tried to re-use the chat room %s, but it was deleted before he clicked the Add button: %s" %(self._aw.getUser().getFullName(), roomID, e))
                    raise NoReportError(_('Some of the rooms were deleted from the other conference(s) they belonged to. Please refresh your browser'))
                room.setConference(ConferenceHolder().getById(self._conference))
                self._notify('addConference2Room', {'room': room, 'conf': self._conference})
                fossilizedRoom = room.fossilizeMultiConference(ConferenceHolder().getById(self._conference))
                # add links to join the room
                fossilizedRoom['custom'] = generateCustomLinks(room)
                # add link to retrieve logs
                fossilizedRoom['logs'] = generateLogLink(room, room.getConferences().values()[0])
                rooms.append(fossilizedRoom)
        except NoReportError, e:
            Logger.get('ext.im').exception("Error adding chat rooms. User: %s. Chat room: %s" %(self._aw.getUser().getFullName(), roomID))
            raise ServiceError(message = _('There was an error trying to add the chat rooms. Please refresh your browser and try again'))
        return rooms


class AddLogs2Material( ServiceBase ):

    def _checkParams(self):
        self._conf = ConferenceHolder().getById(self._params['confId'])
        self._chatroom = DBHelpers.getChatroom(self._params['crId'])
        self._sdate = self._params['sdate'] if self._params.has_key('sdate') else None
        self._edate = self._params['edate'] if self._params.has_key('edate') else None
        self._forEvent = bool(self._params['forEvent']) if self._params.has_key('forEvent') else None
        self._getAll = bool(self._params['getAll']) if self._params.has_key('getAll') else None
        self._matName = self._params['matName']
        self._repositoryId = None

    def getNewId(self):
        # get the list of custom materials
        matList = self._conf.getMaterialList()
        maxId = -1
        for material in matList:
            if int(material.getId()) > maxId:
                maxId = int(material.getId())
        # we want the next id
        return maxId+1

    def _getNewTempFile( self ):
        cfg = Config.getInstance()
        tempPath = cfg.getUploadedFilesTempDir()
        tempFileName = tempfile.mkstemp( suffix="Indico.tmp", dir = tempPath )[1]
        return tempFileName

    #XXX: improve routine to avoid saving in temporary file
    def _saveFileToTemp( self, doc ):
        fileName = self._getNewTempFile()
        f = open( fileName, "wb" )
        f.write( doc )
        f.close()
        return fileName

    def _getAnswer( self ):
        if self._getAll:
            url = LogLinkGenerator(self._chatroom).generate()
        elif self._forEvent:
            url = LogLinkGenerator(self._chatroom).generate(str(self._conf.getStartDate().date()), str(self._conf.getEndDate().date()))
        else:
            url = LogLinkGenerator(self._chatroom).generate(self._sdate, self._edate)

        req = urllib2.Request(url, None, {'Accept-Charset' : 'utf-8'})
        document = urllib2.urlopen(req).read()

        if document is '':
            raise NoReportError(_('No logs were found for these dates'), title='Error')
        # create the file
        fDict = {}
        fDict["filePath"]=self._saveFileToTemp(document)

        self._tempFilesToDelete.append(fDict["filePath"])

        fDict["fileName"]= self._matName+".html"
        fDict["size"] = int(os.stat(fDict["filePath"])[stat.ST_SIZE])
        self._file = fDict

        # create the material
        registry = self._conf.getMaterialRegistry()
        self._materialId = str(self.getNewId())

        #mf = registry.getById(self._materialId)
        mf = registry.getById('logs')
        mat = mf.get(self._conf)
        if mat is None:
            mat = mf.create(self._conf)
            mat.setProtection(1)
            mat.setTitle('Chat room Logs')
            mat.setDescription('Chat logs for this event')

        # create the resource
        resource = LocalFile()
        resource.setFileName(self._file["fileName"])
        resource.setFilePath(self._file["filePath"])
        resource.setDescription("Chat logs for the chat room %s" %self._chatroom.getTitle())
        resource.setName(resource.getFileName())

        log_info = {"subject":"Added file %s%s" % (self._file["fileName"],'')}
        self._conf.getLogHandler().logAction(log_info, log.ModuleNames.MATERIAL)

        # forcedFileId - in case there is a conflict, use the file that is
        # already stored
        mat.addResource(resource, forcedFileId=self._repositoryId)


        # store the repo id, for files
        if isinstance(resource, LocalFile):
            self._repositoryId = resource.getRepositoryId()

        protectedObject = resource
        protectedObject.setProtection(0)

        return mat.getId()


methodMap = {
    "XMPP.createRoom": CreateChatroom,
    "XMPP.editRoom": EditChatroom,
    "XMPP.deleteRoom": DeleteChatroom,
    "XMPP.getRoomPreferences": GetRoomPreferences,
    "XMPP.getRoomsByUser": GetRoomsByUser,
    "XMPP.getNumberOfRoomsByUser": GetNumberOfRoomsByUser,
    "XMPP.addConference2Room": AddConference2Room,
    "XMPP.attachLogs": AddLogs2Material
}

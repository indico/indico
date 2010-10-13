import random
import hashlib
from pytz import timezone, all_timezones
from MaKaC.services.implementation.base import ServiceBase
from MaKaC.services.interface.rpc.handlers import importModule
from MaKaC.common.logger import Logger
from MaKaC.services.implementation.base import ParameterManager
from MaKaC.common.timezoneUtils import nowutc,getAdjustedDate, DisplayTZ
from MaKaC.conference import ConferenceHolder
from persistent import Persistent
from persistent.mapping import PersistentMapping
from MaKaC.plugins.base import PluginsHolder, Observable
from MaKaC.common.fossilize import Fossilizable, fossilizes, fossilize
from MaKaC.plugins.InstantMessaging.Jabber import fossils
from MaKaC.services.interface.rpc.common import ServiceError, NoReportError
from MaKaC.plugins.InstantMessaging.bot import *
from MaKaC.common.Conversion import Conversion
from MaKaC.conference import ConferenceHolder
from MaKaC.plugins.helpers import DBHelpers, PluginFieldsHelper





class ChatRoomBase ( ServiceBase, Observable ):

    def __init__(self, params, remoteHost, session):
        ServiceBase.__init__(self, params, remoteHost, session)
        #we want the data from the Jabber plugin in the InstantMessaging Plugin type
        oh = PluginFieldsHelper('InstantMessaging', 'Jabber')
        self._botJID = oh.getOption('indicoUsername') + '@' + oh.getOption('chatServerHost')
        self._botPass = oh.getOption('indicoPassword')
        self._messages = { 'sameId': _('There is already a chat room with the same id'), \
                           'sameName': _('There is already a chat room in the server with that name, please choose another one'), \
                           'creating': _('There was an error while creating the chat room in the local server. Please try again later'), \
                           'editing': _('There was an error while editing the chat room in the local server. Please try again later'), \
                           'deleting': _('There was an error while deleting the chat room in the Jabber server. Please try to do it manually from your client' \
                                            ' or contact the administrators'), \
                           'connecting': _('There was an error while connecting to the Jabber server. Maybe the username or password are not correct'), \
                           'CRdeletedFromClient': _('Someone deleted the chat room from the Jabber server since this page was loaded. We recommend you to delete the chatroom from Indico as well')
                          }

    def _checkParams(self):
        pm = ParameterManager(self._params)
        self._conferenceID = pm.extract("conference", pType=str, allowEmpty = False)

        pm = ParameterManager(self._params.get('chatroomParams'))
        self._title = pm.extract('title', pType=str, allowEmpty = False)
        self._description = pm.extract('description', pType=str, allowEmpty = True)
        self._createRoom = pm.extract('createRoom', pType=str, allowEmpty = True)
        if self._createRoom == 'yes':
            self._createRoom = True
            oh = PluginFieldsHelper('InstantMessaging', 'Jabber')
            self._host = oh.getOption('chatServerHost')
        elif self._createRoom == 'no':
            self._host = pm.extract('host', pType=str, allowEmpty = False)
            self._createRoom = False
        else:
            raise Exception('No value found in the field to specify a new chat room or define an existing one')

        self._password = pm.extract('roomPass', pType=str, allowEmpty = True, defaultValue='')

        self._showRoom = pm.extract('showRoom', pType=list, allowEmpty = True)
        if len(self._showRoom) is 0:
            self._showRoom = False
        else:
            self._showRoom = True

        self._showPass = pm.extract('showPass', pType=list, allowEmpty = True)
        if len(self._showPass) is 0:
            self._showPass = False
        else:
            self._showPass = True

    def createRoomJabber(self, jid, password, room):
        """ Creates the room in the Jabber server """
        try:
            self._bot = IndicoJabberBotCreateRoom(jid, password, room)
        except Exception, e:
            raise NoReportError( self._messages['creating'])
        if hasattr(self._bot, '_error') and self._bot._error:
            raise NoReportError( self._messages['creating'])
        elif not hasattr(self._bot, '_error'):
            raise NoReportError( self._messages['connecting'])
        return True

    def editRoomJabber(self, jid, password, room):
        """ Edits the room in the Jabber server """
        try:
            self._bot = IndicoJabberBotEditRoom(jid, password, room)
        except Exception, e:
            Logger.get('InstantMessaging (Jabber)').info("Exception while editing: %s" %e)
            raise NoReportError( self._messages['editing'])
        if hasattr(self._bot, '_error') and self._bot._error:
            Logger.get('InstantMessaging (Jabber)').info("Exception while editing: Apparently there was a problem with the XMPP library")
            raise NoReportError( self._messages['editing'])
        elif not hasattr(self._bot, '_error'):
            raise NoReportError( self._messages['connecting'])
        return True

    def deleteRoomJabber(self, jid, password, room, message):
        """ Deletes the room in the Jabber server """
        message = "%s has requested to delete this room. The host for the new chat room is %s, please reconnect there" %(self._user.getName(), self._host)
        try:
            self._bot = IndicoJabberBotDeleteRoom(jid, password, room, message)
        except Exception, e:
            raise NoReportError( self._messages['deleting'])
        if hasattr(self._bot, '_error') and self._bot._error:
            raise NoReportError( self._messages['deleting'])
        elif not hasattr(self._bot, '_error'):
            raise NoReportError( self._messages['connecting'])
        return True



class CreateChatroom( ChatRoomBase ):

    def __init__(self, params, remoteHost, session):
        ChatRoomBase.__init__(self, params, remoteHost, session)

    def _checkParams(self):
        ChatRoomBase._checkParams(self)
        self._user = self._getUser()

    def _getAnswer( self ):
        self._room = Chatroom(self._title, \
                              self._user, \
                              ConferenceHolder().getById(self._conferenceID), \
                              None, \
                              self._description, \
                              self._createRoom, \
                              self._host, \
                              self._password, \
                              self._showRoom, \
                              self._showPass)
        try:
            self._notify('createChatroom', self._room)
        except ServiceError, e:
            raise ServiceError( message=self._messages['sameId'] )
        except NoReportError, e:
            raise NoReportError(self._messages['sameName'], explanation='roomExists')
        except Exception, e:
            raise ServiceError( message=str(e) )

        if self._room.getCreateRoom():
            #if we're not creating the room in our server we don't need to call the bot
            self.createRoomJabber(self._botJID, self._botPass, self._room)

        Logger.get('InstantMessaging (Jabber)').info("The room %s has been created by the user %s at %s hours" %(self._title, self._user.getName(), self._room.getModificationDate()))

        tz = DisplayTZ(self._aw, self._room.getConference()).getDisplayTZ()
        return self._room.fossilize(tz=tz)



class EditChatroom( ChatRoomBase ):

    def __init__(self, params, remoteHost, session):
        ChatRoomBase.__init__(self, params, remoteHost, session)

    def _checkParams(self):
        ChatRoomBase._checkParams(self)

        pm = ParameterManager(self._params.get('chatroomParams'))
        self._id = pm.extract('id', pType=str, allowEmpty = False)
        self._user = self._getUser()
        self._modificationDate = nowutc()

    def _getAnswer( self ):
        values = {'title':self._title, \
                  'user':self._user, \
                  'modificationDate':self._modificationDate, \
                  'description':self._description, \
                  'createRoom':self._createRoom, \
                  'host':self._host, \
                  'password':self._password, \
                  'showRoom':self._showRoom, \
                  'showPass':self._showPass, \
                  'conference':ConferenceHolder().getById(self._conferenceID) \
                  }
        try:
            self._room = DBHelpers().getChatroom(self._id)
            oldRoom = Chatroom(self._room.getTitle(), self._room.getOwner(), ConferenceHolder().getById(self._conferenceID))

            self._room.setValues(values)
            #edit the chat room in indico
            self._notify('editChatroom', {'oldTitle': oldRoom.getTitle(), 'newRoom':self._room})
        except ServiceError, e:
            raise ServiceError( message=_('Problem while accessing the database: %s' %e))
        except Exception, e:
            Logger.get('InstantMessaging (Jabber)').info("Exception while editing: %s" %e)
            raise NoReportError( self._messages['editing'], explanation='roomExists')

        modified = False
        if oldRoom.getTitle() != self._room.getTitle() and oldRoom.getCreateRoom() and self._room.getCreateRoom():
            #before, the chat room was in the Jabber server. After editing, it is still in the Jabber server, but the title has changed.
            #This means that we'll have to delete the old room and create the new one with the new title
            message = "%s has requested to delete this room. The new chat room name is %s, please reconnect there" %(self._user.getName(), self._title)
            modified = self.deleteRoomJabber(self._botJID, self._botPass, oldRoom, message)
            modified = self.createRoomJabber(self._botJID, self._botPass, self._room)

        else:
            #before, the room had to be created in the Jabber server, after the modification a different server will be used
            if oldRoom.getCreateRoom() and not self._room.getCreateRoom():
                #delete the existing room in the Jabber server
                message = "%s has requested to delete this room. The host for the new chat room is %s, please reconnect there" %(self._user.getName(), self._host)
                modified = self.deleteRoomJabber(self._botJID, self._botPass, oldRoom, message)

            #before, the room was in an external server, now it's in the Jabber server
            elif not oldRoom.getCreateRoom() and self._room.getCreateRoom():
                #create the room in the Jabber server
                modified = self.createRoomJabber(self._botJID, self._botPass, self._room)

            #no changes were made in this area, we edit the room in case it's created in the Jabber server
            elif self._room.getCreateRoom():
                modified = self.editRoomJabber(self._botJID, self._botPass, self._room)

        if modified:
            Logger.get('InstantMessaging (Jabber)').info("The room %s has been modified by the user %s at %s hours" %(self._title, self._user.getName(), self._room.getModificationDate()))

        return self._room.fossilizeMultiConference(values['conference'])



class DeleteChatroom( ChatRoomBase ):

    def __init__(self, params, remoteHost, session):
        ChatRoomBase.__init__(self, params, remoteHost, session)

    def _checkParams(self):
        ChatRoomBase._checkParams(self)
        pm = ParameterManager(self._params.get('chatroomParams'))
        self._id = pm.extract('id', pType=str, allowEmpty = False)
        self._room = DBHelpers().getChatroom(self._id)
        self._user = self._getUser()

    def _getAnswer( self ):
        message = _("%s has requested to delete this room. Please address this person for further information" %self._user.getName())
        #delete room from Indico
        try:
            self._notify('deleteChatroom', self._room)
        except ServiceError, e:
            raise ServiceError( message=_('Problem deleting indexes in the database for chat room %s: %s' %(self._room.getTitle(), e)))

        #delete room from our Jabber server (if neccesary)
        if self._room.getCreateRoom() and len(self._room.getConferences()) is 0:
            self.deleteRoomJabber(self._botJID, self._botPass, self._room, message)

        Logger.get('InstantMessaging (Jabber)').info("The room %s has been deleted by the user %s at %s hours" %(self._title, self._user.getName(), nowutc()))

        return True


class GetRoomPreferences( ChatRoomBase ):

    def __init__(self, params, remoteHost, session):
        ChatRoomBase.__init__(self, params, remoteHost, session)

    def _checkParams(self):
        ChatRoomBase._checkParams(self)
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
            raise ServiceError( message=_('Error trying to get the chat room preferences'))

        self._bot = IndicoJabberBotGetPreferences(self._botJID, self._botPass, self._room)

        if hasattr(self._bot, '_error') and self._bot._error:
            raise NoReportError(self._messages['CRdeletedFromClient'])

        #get the preferences and check updates
        for preference in self._bot._form.fields:
            if preference.var in fieldsToCheck.keys():
                #we execute setTitle, setDescription or setPassword with the new value
                getattr(self._room, 'set'+ fieldsToCheck[preference.var])(preference.value.pop())

        return self._room.fossilize()


class GetRoomsByUser( ServiceBase ):

    def __init__(self, params, remoteHost, session):
        ServiceBase.__init__(self, params, remoteHost, session)

    def _checkParams(self):
        self._user = self._params['usr']

    def _getAnswer( self ):
        return fossilize(DBHelpers().getRoomsByUser(self._user))



class AddConference2Room( ServiceBase, Observable ):

    def __init__(self, params, remoteHost, session):
        ServiceBase.__init__(self, params, remoteHost, session)

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
                    raise NoReportError('Some of the rooms were deleted from the other conference(s) they belonged to. Please refresh your browser')
                room.setConference(ConferenceHolder().getById(self._conference))
                self._notify('addConference2Room', room)
                rooms.append(room.fossilizeMultiConference(ConferenceHolder().getById(self._conference)))
        except NoReportError, e:
            raise NoReportError('There was an error trying to add the chat rooms. Please refresh your browser and try again')
        return rooms




class Chatroom (Persistent, Fossilizable):

    fossilizes(fossils.IChatRoomFossil)

    def __init__( self, name, owner, conference, modificationDate=None, description='',createRoom=True, host='', password='', showRoom=False, showPass=False ):
        Persistent.__init__(self)
        self._name = name
        self._owner = owner
        self._creationDate = nowutc()
        self._conference = PersistentMapping()#{}
        self._conference[conference.getId()] = conference
        self._modificationDate = modificationDate
        self._description = description
        self._createRoom = createRoom
        self._host = host
        self._password = password
        self._showRoom = showRoom
        self._showPass = showPass
        #the id will be assigned just before being stored in the DB.
        #If we try to create a counter now it will fail if it's the first chatroom
        #in the conference, since no indexes have been created yet
        self._id = None

    def __cmp__( self, obj ):
        """ Needed to make internal comparisons in the OOTreeSet. Otherwise we may get some KeyErrors when trying to delete chat rooms"""
        return cmp( self._id, obj.getId() )

    def setValues(self, values):
        self._name = values['title']
        self._owner = values['user']
        #it has to be a dictionary with conferences, otherwise it'll make everything go wrong
        self._conference[values['conference'].getId()] = values['conference']
        self._modificationDate = values['modificationDate']
        self._description = values['description']
        self._createRoom = values['createRoom']
        self._host = values['host']
        self._password = values['password']
        self._showRoom = values['showRoom']
        self._showPass = values['showPass']

    def setTitle(self, name):
        self._name = name

    def getTitle(self):
        return self._name

    def setHost(self, host):
        self._host = host

    def getHost(self):
        return self._host

    def setOwner(self, owner):
        self._owner = owner

    def getOwner(self):
        return self._owner

    def setCreationDate(self, date):
        self._creationDate = date

    def getCreationDate(self):
        return self._creationDate

    def getAdjustedCreationDate(self,tz=None):
        if not tz or tz not in all_timezones:
            tz = 'UTC'
        return self.getCreationDate().astimezone(timezone(tz))

    def setDescription(self, description):
        self._description = description

    def getDescription(self):
        return self._description

    def setCreateRoom(self, createRoom):
        self._createRoom = createRoom

    def getCreateRoom(self):
        return self._createRoom

    def setPassword(self, password):
        self._password = password

    def getPassword(self):
        return self._password

    def setShowRoom(self, showRoom):
        self._showRoom = showRoom

    def getShowRoom(self):
        return self._showRoom

    def setShowPass(self, showPass):
        self._showPass = showPass

    def getShowPass(self):
        return self._showPass

    def setModificationDate(self, date):
        self._modificationDate = date

    def getModificationDate(self):
        return self._modificationDate

    def getAdjustedModificationDate(self,tz=None):
        if not self.getModificationDate():
            return None
        if not tz or tz not in all_timezones:
            tz = 'UTC'
        return self.getModificationDate().astimezone(timezone(tz))

    def setConference(self, conference):
        if len(self._conference) is 0:
            self._conference = PersistentMapping()
        self._conference[conference.getId()] = conference

    def getConference(self):
        """ If there's only one conference in the dictionary it returns the conference itself, otherwise returns the dictionary"""
        if len(self._conference) is 1:
            return self._conference.values()[0]
        elif len(self._conference) >1:
            return self._conference
        else:
            raise ServiceError(message='No conferences found in the chat room %s'%self._name)

    def getConferences(self):
        """ returns always the dictionary"""
        return self._conference

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id

    def fossilizeMultiConference(self, conference):
        """Since we may have more than 1 conference for the same chat room we cannot know to which timezone should we adjust the dates when fossilizing.
        Therefore, we do it manually with the conference given in the request"""
        fossilizedRoom = self.fossilize()
        tz=conference.getTimezone()
        fossilizedRoom['creationDate'] = Conversion().datetime(self._creationDate.astimezone(timezone(tz)), tz)
        if self._modificationDate:
            fossilizedRoom['modificationDate'] = Conversion().datetime(self._modificationDate.astimezone(timezone(tz)), tz)
        return fossilizedRoom


methodMap = {
    "jabber.createRoom": CreateChatroom,
    "jabber.editRoom": EditChatroom,
    "jabber.deleteRoom": DeleteChatroom,
    "jabber.getRoomPreferences": GetRoomPreferences,
    "jabber.getRoomsByUser": GetRoomsByUser,
    "jabber.addConference2Room": AddConference2Room
}
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
from MaKaC.common.logger import Logger


try:
    import sleekxmpp
except ImportError:
    Logger.get("XMPP").error("Missing sleekxmpp python library")
    raise

from MaKaC.i18n import _

class IndicoXMPPBotBase(object):

    def __init__(self, jid, password):
        self.xmpp = sleekxmpp.ClientXMPP(jid, password)
        self.xmpp.registerPlugin('xep_0045')
        self.xmpp.registerPlugin('xep_0004')
        self.xmpp.registerPlugin('xep_0030')
        self.xmpp.add_event_handler("session_start", self.handleXMPPConnected)

    def formDefaults(self, form):
        form.addField(var = 'muc#roomconfig_publicroom', value = '1')
        form.addField(var = 'public_list', value = '1')
        form.addField(var = 'muc#roomconfig_whois', value = 'moderators')
        form.addField(var = 'muc#roomconfig_membersonly', value = '0')
        form.addField(var = 'muc#roomconfig_moderatedroom', value = '1')
        form.addField(var = 'members_by_default', value = '1')
        form.addField(var = 'muc#roomconfig_changesubject', value = '1')
        form.addField(var = 'allow_private_messages', value = '1')
        form.addField(var = 'allow_query_users', value = '1')
        form.addField(var = 'muc#roomconfig_allowinvites', value = '1')
        form.addField(var = 'muc#roomconfig_allowvisitorstatus', value = '1')
        form.addField(var = 'muc#roomconfig_allowvisitornickchange', value = '1')
        form.addField(var = 'muc#roomconfig_enablelogging', value = '1')
        #form.addField(var = 'muc#roomconfig_maxusers', value = '1000')

    def handleXMPPConnected(self, event):
        pass

    def treatError(self, error, msg=''):
        """ Gets the response from the XMPP driver and, in case of error, returns the appropiate message"""
        return {'error': error,
                'reason': msg if msg!= '' else _('There was a problem while connecting our XMPP server. Please try again later')}

    def run(self):
        self.xmpp.process(threaded=False)


class IndicoXMPPBotRoomExists(IndicoXMPPBotBase):

    def __init__(self, jid, password, room):
        IndicoXMPPBotBase.__init__(self, jid, password)
        self._room = room
        self._protected = 1 if self._room.getPassword() != '' else 0
        self._nick, server = jid.split('@')
        self._jid = self._room.getTitle() + '@conference.' + server
        try:
            connected = self.xmpp.connect()
        except Exception, e:
            Logger.get('xmpp').exception('Connection problem')
            self._error = self.treatError(True, str(e))
            self.xmpp.disconnect()

    def handleXMPPConnected(self, event):
        #mod_discovery, service discovery related
        disco = self.xmpp.plugin['xep_0030']
        try:
            disco.getInfo(self._jid)
            self._error = self.treatError(True, 'roomExists')
        except sleekxmpp.exceptions.IqError, e:
            if e.condition == 'item-not-found':
                self._error = self.treatError(False)
            else:
                self._error = self.treatError(True, str(e))
        except Exception, e:
            Logger.get('xmpp').exception('Error connecting')
            self._error = self.treatError(True, str(e))
        finally:
            self.xmpp.disconnect()



class IndicoXMPPBotCreateRoom(IndicoXMPPBotBase):

    def __init__(self, jid, password, room):
        IndicoXMPPBotBase.__init__(self, jid, password)
        self._room = room
        self._protected = 1 if self._room.getPassword() != '' else 0
        self._nick, server = jid.split('@')
        self._jid = self._room.getTitle() + '@conference.' + server

        try:
            connected = self.xmpp.connect()
        except Exception, e:
            self._error = self.treatError(True, str(e))
            self.xmpp.disconnect()
        #self.xmpp.process(threaded=False)

    def handleXMPPConnected(self, event):
        #mod_muc, multi chat related
        muc = self.xmpp.plugin['xep_0045']

        try:
            muc.joinMUC(room = self._jid, nick = self._nick)
        except Exception, e:
            self._error = self.treatError(True, str(e))
            self.xmpp.disconnect()
        form = self.xmpp.plugin['xep_0004'].makeForm(ftype='submit')

        form.addField('FORM_TYPE', value='http://jabber.org/protocol/muc#roomconfig')
        self.formDefaults(form)
        form.addField(var = 'muc#roomconfig_roomname', value = self._room.getTitle())

        #FYI: If a field is empty eXMPPd will answer with a bad request error, so if the field's value is empty do not send it!
        if self._room.getDescription():
            form.addField(var = 'muc#roomconfig_roomdesc', value = self._room.getDescription())
        if self._protected:
            form.addField(var = 'muc#roomconfig_passwordprotectedroom', value = str(self._protected))
            form.addField(var = 'muc#roomconfig_roomsecret', value = self._room.getPassword())

        form.addField(var = 'muc#roomconfig_persistentroom', value = '1')

        try:
            self._error = self.treatError(not muc.configureRoom(self._jid, form))
        except Exception, e:
            self._error = self.treatError(True, str(e))
            self.xmpp.disconnect()

        self.xmpp.disconnect()


class IndicoXMPPBotEditRoom(IndicoXMPPBotBase):

    def __init__(self, jid, password, room, checkRoomExists):
        IndicoXMPPBotBase.__init__(self, jid, password)
        self._room = room
        self._protected = 1 if self._room.getPassword() != '' else 0
        self._nick, server = jid.split('@')
        self._jid = self._room.getTitle() + '@conference.' + server
        self._checkRoomExists = checkRoomExists
        self._error = False

        try:
            self.xmpp.connect()
        except Exception, e:
            self._error = self.treatError(True, str(e))
            self.xmpp.disconnect()
        #self.xmpp.process(threaded=False)

    def handleXMPPConnected(self, event):
        #mod_muc, multi chat related
        muc = self.xmpp.plugin['xep_0045']

        try:
            muc.joinMUC(room = self._jid, nick = self._nick)
        except Exception, e:
            self._error = self.treatError(True, str(e))
            self.xmpp.disconnect()

        form = self.xmpp.plugin['xep_0004'].makeForm(ftype='submit')

        form.addField('FORM_TYPE', value='http://jabber.org/protocol/muc#roomconfig')
        self.formDefaults(form)
        form.addField(var = 'muc#roomconfig_roomname', value = self._room.getTitle())

        #FYI: If a field is empty ejabberd will answer with a bad request error, so if the field's value is empty do not send it!
        if self._room.getDescription() and self._room.getDescription() != '':
            form.addField(var = 'muc#roomconfig_roomdesc', value = self._room.getDescription())
        form.addField(var = 'muc#roomconfig_passwordprotectedroom', value = str(self._protected))
        if self._protected and self._room.getPassword() != '':
            form.addField(var = 'muc#roomconfig_roomsecret', value = self._room.getPassword())

        form.addField(var = 'muc#roomconfig_persistentroom', value = '1')

        try:
            self._error = self.treatError(not muc.configureRoom(self._jid, form))
        except Exception, e:
            self._error = self.treatError(True, str(e))
            self.xmpp.disconnect()

        self.xmpp.disconnect()


class IndicoXMPPBotDeleteRoom(IndicoXMPPBotBase):

    def __init__(self, jid, password, room, reason):
        IndicoXMPPBotBase.__init__(self, jid, password)
        self._room = room
        self._protected = 1 if self._room.getPassword() != '' else 0
        self._nick, server = jid.split('@')
        self._jid = self._room.getTitle() + '@conference.' + server
        self._reason = reason
        self._error = False

        try:
            self.xmpp.connect()
        except Exception, e:
            self._error = self.treatError(True, str(e))
            self.xmpp.disconnect()
        #self.xmpp.process(threaded=False)

    def handleXMPPConnected(self, event):
        muc = self.xmpp.plugin['xep_0045']
        try:
            muc.joinMUC(room = self._jid, nick = self._nick)
        except Exception, e:
            self._error = self.treatError(True, str(e))
            self.xmpp.disconnect()

        try:
            self.xmpp.sendMessage(self._jid, self._reason, mtype='groupchat')
            self._error = self.treatError(not muc.destroy(self._jid, self._reason))
        except Exception, e:
            self._error = self.treatError(True, str(e))
            self.xmpp.disconnect()

        self.xmpp.disconnect()


class IndicoXMPPBotGetPreferences(IndicoXMPPBotBase):

    def __init__(self, jid, password, room):
        IndicoXMPPBotBase.__init__(self, jid, password)
        self._room = room
        self._nick, server = jid.split('@')
        self._jid = self._room.getTitle() + '@conference.' + server

        try:
            self.xmpp.connect()
        except Exception, e:
            self._error = self.treatError(True, str(e))
            self.xmpp.disconnect()
        #self.xmpp.process(threaded=False)

    def handleXMPPConnected(self, event):
        muc = self.xmpp.plugin['xep_0045']
        try:
            self._form = muc.getRoomConfig(self._jid)
        except Exception, e:
            self._error = self.treatError(True, str(e))
            self.xmpp.disconnect()
        self._error = self.treatError(False)

        self.xmpp.disconnect()

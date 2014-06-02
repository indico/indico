# -*- coding: utf-8 -*-
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

import re
from MaKaC.plugins.util import PluginFieldsWrapper
from MaKaC.plugins.InstantMessaging.urlHandlers import UHConfModifChatSeeLogs


class LinkGenerator:
    """ Generates links to xmpp chat rooms """

    def __init__(self, chatroom):
        self._chatroom = chatroom

    def generate(self):
        pass


class GeneralLinkGenerator(LinkGenerator):

    def __init__(self, chatroom, structure, nick=None):
        LinkGenerator.__init__(self, chatroom)
        self._structure = structure
        self._nick = nick

    def generate(self):
        link = re.sub('\[chatroom\]', self._chatroom.getTitle().lower(), self._structure)
        link = re.sub('\[host\]', self._chatroom.getHost(), link)

        if self._nick:
            link = re.sub('\[nickname\]', self._nick, link)

        return link


def generateCustomLinks(chatroom):
    linkList = PluginFieldsWrapper('InstantMessaging').getOption('customLinks')

    result = []
    for link in linkList:
        result.append({'name': link['name'],
                       'link': GeneralLinkGenerator(chatroom,
                                                    link['structure']).generate()
                       })
    return result


def generateLogLink(chatroom, conf):
    if XMPPLogsActivated():
        url = UHConfModifChatSeeLogs.getURL(conf)
        url.addParam('chatroom', chatroom.getId())
        return str(url)
    else:
        return None


def XMPPLogsActivated():
    return PluginFieldsWrapper('InstantMessaging', 'XMPP').getOption('activateLogs')


def addLink(var, linkName, link, chatroomId):
    """ Adds a link to the chat room if it's specified to do so"""
    clink = {}
    clink['name'] = linkName
    clink['link'] = link
    var.append(clink)


class WebLinkGenerator(LinkGenerator):

    def __init__(self, chatroom):
        LinkGenerator.__init__(self, chatroom)
        self._anon = False

    def generate(self):
        # chat rooms in XMPP are created using only lower case, so we convert all to lowercase
        if self._anon:
            return 'https://'+ self._chatroom.getHost()+ '/?r=' +self._chatroom.getTitle().lower()+'@conference.'+self._chatroom.getHost()+'?join'
        else:
            return 'https://'+ self._chatroom.getHost()+ '/?x=' +self._chatroom.getTitle().lower()+'@conference.'+self._chatroom.getHost()+'?join'

    def isActive(self):
        return PluginFieldsWrapper('InstantMessaging', 'XMPP').getOption('joinWebClient')


class DesktopLinkGenerator(LinkGenerator):

    def __init__(self, chatroom):
        LinkGenerator.__init__(self, chatroom)

    def generate(self):
        # chat rooms in XMPP are created using only lower case, so we convert all to lowercase
        return 'xmpp:'+ self._chatroom.getTitle().lower()+'@'+self._chatroom.getHost()+'?join'

    def isActive(self):
        return PluginFieldsWrapper('InstantMessaging', 'XMPP').getOption('joinDesktopClients')


class LogLinkGenerator(LinkGenerator):

    def __init__(self, chatroom):
        LinkGenerator.__init__(self, chatroom)

    def generate(self, sDate = None, eDate = None):
        dates = ''
        if sDate != None:
            dates = '&sdate='+sDate
        elif eDate != None:
            dates = '&edate='+eDate
        if eDate != None and sDate != None:
            dates += '&edate='+eDate
        return 'https://'+ \
                PluginFieldsWrapper('InstantMessaging', 'XMPP').getOption('chatServerHost') + \
                '/logs/?cr=' + \
                self._chatroom.getTitle().lower() + \
                '@conference.' + \
                self._chatroom.getHost() + \
                dates


class DeleteLogLinkGenerator(LinkGenerator):
    def __init__(self, chatroom):
        LinkGenerator.__init__(self, chatroom)

    def generate(self):
        return 'https://'+ \
                PluginFieldsWrapper('InstantMessaging', 'XMPP').getOption('chatServerHost') + \
                '/logs/delete?cr=' + \
                self._chatroom.getTitle() + \
                '@conference.' + \
                self._chatroom.getHost()

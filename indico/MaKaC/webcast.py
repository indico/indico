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

from persistent import Persistent
from MaKaC.common.db import DBMgr
from MaKaC.common.logger import Logger
from MaKaC.common.httpTimeout import urlOpenWithTimeout
from MaKaC.errors import MaKaCError
from urllib2 import HTTPError, URLError
from BaseHTTPServer import BaseHTTPRequestHandler

class WebcastManager(Persistent):
    """Holds and manages general information about webcasts in the system
    """

    def __init__(self):
        self.channels = []
#        self._requested_webcasts = []
        self._archived_webcasts = []
        self._forthcoming_webcasts = []
        self._managers = []
        self._webcastServiceURL = '' #used for forthcoming webcast display
        self._webcastSynchronizationURL = '' #used for automatic synchronization
        
    def getManagers( self ):
        try:
            return self._managers
        except:
            self._managers = []
            return self._managers

    def addManager( self, av ):
        if av not in self.getManagers():
            self._managers.append(av)
            self._p_changed=1

    def removeManager( self, av ):
        if av in self.getManagers():
            self._managers.remove( av )
            self._p_changed=1

    def isManager( self, av ):
        if av in self.getManagers():
            return True
        else:
            return False

    def getChannels(self):
        return self.channels

    def getChannel(self, name):
        for ch in self.channels:
            if ch.getName() == name:
                return ch
        return None

#    def addRequestedWebcast(self, event ):
#        if not self.getRequestedWebcast(event):
#            if event:
#                wc = Webcast(event)
#                self._requested_webcasts.append(wc)
#                self._p_changed=1
#    
#    def getRequestedWebcast(self, event):
#        for wc in self._requested_webcasts:
#            if wc.getEvent() == event:
#                return wc
#        return None
#
#    def getRequestedWebcasts(self):
#        return self._requested_webcasts
#    
#    def acceptRequestedWebcast(self, webcast):
#        for wc in self._requested_webcasts:
#            if wc == webcast:
#                self._requested_webcasts.remove(webcast)
#                if not self.getForthcomingWebcast(webcast.getEvent()):
#                    self._forthcoming_webcasts.append(webcast)
#                self._p_changed=1
#
#    def deleteRequestedWebcast(self, webcast):
#        for wc in self._requested_webcasts:
#            if wc == webcast:
#                self._requested_webcasts.remove(webcast)
#                self._p_changed=1
                    
    def addForthcomingWebcast( self, event):
        if not self.getForthcomingWebcast(event):
            if event:
                wc = Webcast(event)
                self._forthcoming_webcasts.append(wc)
                self._p_changed=1
                self.remoteSynchronize()
            
    def getForthcomingWebcast(self, event):
        for wc in self._forthcoming_webcasts:
            if wc.getEvent() == event:
                return wc
        return None

    def getForthcomingWebcastById(self, id):
        for wc in self._forthcoming_webcasts:
            if wc.getId() == id:
                return wc
        return None

    def getWebcasts(self):
        return self.getArchivedWebcasts() + self.getForthcomingWebcasts()

    def getForthcomingWebcasts(self):
        return self._forthcoming_webcasts
    
    def archiveForthcomingWebcast(self, webcast):
        for wc in self._forthcoming_webcasts:
            if wc == webcast:
                self._forthcoming_webcasts.remove(webcast)
                if not self.getArchivedWebcast(webcast.getEvent()):
                    self._archived_webcasts.append(webcast)
                self._p_changed=1
                self.remoteSynchronize()

    def archiveForthcomingWebcastById(self, id):
        for wc in self._forthcoming_webcasts:
            if wc.getId() == id:
                self._forthcoming_webcasts.remove(wc)
                if not self.getArchivedWebcast(wc.getEvent()):
                    self._archived_webcasts.append(wc)
                self._p_changed=1
                self.remoteSynchronize()
       
    def unArchiveWebcastById(self, id):
        for wc in self._archived_webcasts:
            if wc.getId() == id:
                self._archived_webcasts.remove(wc)
                if not self.getForthcomingWebcast(wc.getEvent()):
                    self._forthcoming_webcasts.append(wc)
                self._p_changed=1
                self.remoteSynchronize()
                
    def deleteForthcomingWebcast(self, webcast):
        for wc in self._forthcoming_webcasts:
            if wc == webcast:
                self._forthcoming_webcasts.remove(webcast)
                self._p_changed=1
                self.remoteSynchronize()
                return True
        return False
              
    def deleteForthcomingWebcastById(self, id):
        for wc in self._forthcoming_webcasts:
            if wc.getId() == id:
                self._forthcoming_webcasts.remove(wc)
                self._p_changed=1
                self.remoteSynchronize()
                return True
        return False
                
    def addArchivedWebcast( self, event ):
        if not self.getArchivedWebcast(event):
            if event:
                wc = Webcast(event)
                self._archived_webcasts.append(wc)
                self._p_changed=1
                self.remoteSynchronize()
            
    def getArchivedWebcast(self, event):
        for wc in self._archived_webcasts:
            if wc.getEvent() == event:
                return wc
        return None

    def getArchivedWebcasts(self):
        return self._archived_webcasts
    
    def deleteArchivedWebcast(self, webcast):
        for wc in self._archived_webcasts:
            if wc == webcast:
                self._archived_webcasts.remove(webcast)
                self._p_changed=1
                return True
        return False

    def deleteArchivedWebcastById(self, id):
        for wc in self._archived_webcasts:
            if wc.getId() == id:
                self._archived_webcasts.remove(wc)
                self._p_changed=1
                return True
        return False
                
    def setOnAir(self, chname, webcast):
        ch = self.getChannel(chname)
        if ch:
            ch.setOnAir(webcast)
            self.remoteSynchronize()

    def whatsOnAir( self ):
        onair = []
        for ch in self.getChannels():
            if ch.whatsOnAir() != None:
                onair.append(ch.whatsOnAir())
        return onair

    def isOnAir( self, event ):
        for ch in self.getChannels():
            if ch.whatsOnAir() != None:
                if ch.whatsOnAir().getId() == event.getId():
                    return ch.getURL()
        return None
            
    def removeFromAir(self, chname):
        ch = self.getChannel(chname)
        if ch:
            ch.setOnAir(None)
            self.remoteSynchronize()
            
    def addChannel(self, name, url, width=480, height=360):
        if name != "" and not self.getChannel(name):
            ch = Channel(name, url, width, height)
            self.channels.append(ch)
            self._p_changed=1
            self.remoteSynchronize()
        
    def removeChannel(self, name):
        for ch in self.channels:
            if ch.getName() == name:
                self.channels.remove(ch)
                self._p_changed=1
                self.remoteSynchronize()
        
    def switchChannel(self, name):
        for ch in self.channels:
            if ch.getName() == name:
                ch.switchOnAir()
                self._p_changed=1
                self.remoteSynchronize()

    def moveChannelUp(self, nb):
        if len(self.channels) <= 1 or len(self.channels) < nb:
            return False
        tomove = self.channels.pop(nb)
        if nb == 0:
            self.channels.append(tomove)
        else:
            self.channels.insert(nb-1, tomove)
        self._p_changed=1
        self.remoteSynchronize()
        return True

    def moveChannelDown(self, nb):
        if len(self.channels) <= 1 or len(self.channels) < nb:
            return False
        tomove = self.channels.pop(nb)
        if nb == len(self.channels):
            self.channels.insert(0, tomove)
        else:
            self.channels.insert(nb+1, tomove)
        self._p_changed=1
        self.remoteSynchronize()
        return True
    
    def getWebcastServiceURL(self):
        """ Returns the Webcast Service URL ( a string ).
            It will be used to display a link when an event is a forthcoming webcast.
        """
        if not hasattr(self, "_webcastServiceURL"):
            self._webcastServiceURL = ''
        return self._webcastServiceURL
    
    def setWebcastServiceURL(self, url):
        """ Sets the Webcast Service URL ( a string ).
        """
        self._webcastServiceURL = url
        
    def getWebcastSynchronizationURL(self):
        """ Returns the Webcast Synchronization URL ( a string ).
            It will be used to automatically synchronize every time a 'live channel' is modified
            or an event is added / removed from forthcoming webcasts
        """
        if not hasattr(self, "_webcastSynchronizationURL"):
            self._webcastSynchronizationURL = ''
        return self._webcastSynchronizationURL
    
    def setWebcastSynchronizationURL(self, url):
        """ Sets the Webcast Synchronization URL ( a string ).
        """
        self._webcastSynchronizationURL = url
        
    def remoteSynchronize(self, raiseExceptionOnSyncFail = False):
        """ Calls the webcast synchronization URL
            Will perform an intermediate commit before calling the URL
            or the remote server will query a non-updated state of the indico DB.
            
            raiseExceptionOnSyncFail: if True (default), we will raise a MaKaCError if calling the webcast
            synchronization URL had a problem
        """
        url = str(self.getWebcastSynchronizationURL()).strip()
        if url:
            
            try:
                Logger.get('webcast').info("Doing an intermediate commit...")
                DBMgr.getInstance().commit()
                Logger.get('webcast').info("Commit done.")
                Logger.get('webcast').info("Calling the webcast synchronization URL: " + url)
                answer = urlOpenWithTimeout(url , 10).read(100000).strip()
                Logger.get('webcast').info("Got answer: " + answer)
                return answer
                
            except HTTPError, e:
                code = e.code
                shortMessage = BaseHTTPRequestHandler.responses[code][0]
                longMessage = BaseHTTPRequestHandler.responses[code][1]
                
                Logger.get('webcast').error("""Calling the webcast synchronization URL: [%s] triggered HTTPError: %s (code = %s, shortMessage = '%s', longMessage = '%s'""" % (str(url), str(e), code, shortMessage, longMessage))
                
                if raiseExceptionOnSyncFail:
                    if str(code) == '404':
                        raise MaKaCError('Could not find the server at ' + str(url) + "(HTTP error 404)", 'webcast')
                    elif str(code) == '500':
                        raise MaKaCError("The server at" + str(url) + " has an internal problem (HTTP error 500)", 'webcast')
                    else:
                        raise MaKaCError("Problem contacting the webcast synchronization server. Reason: HTTPError: %s (code = %s, shortMessage = '%s', longMessage = '%s', url = '%s'""" % (str(e), code, shortMessage, longMessage, str(url)), 'webcast')
                
            except URLError, e:
                Logger.get('webcast').error("""Calling the webcast synchronization URL: [%s] triggered exception: %s""" % (str(url), str(e)))
                if raiseExceptionOnSyncFail:
                    if str(e.reason).strip() == 'timed out':
                        raise MaKaCError("The webcast synchronization URL is not responding", 'webcast')
                    raise MaKaCError("""URLError when contacting the webcast synchronization URL: [%s]. Reason=[%s]"""%(str(url), str(e.reason)), 'webcast')
                
            except ValueError, e:
                Logger.get('webcast').error("""Calling the webcast synchronization URL: [%s] triggered ValueError: %s""" % (str(url), str(e)))
                if raiseExceptionOnSyncFail:
                    if str(e.args[0]).strip().startswith("unknown url type"):
                        raise MaKaCError("The webcast synchronization is not of a correct type. Perhaps you forgot the http:// ?", 'webcast')
                    raise MaKaCError("""Calling the webcast synchronization URL: [%s] triggered ValueError: %s""" % (str(url), str(e)), 'webcast')
                
            except Exception, e:
                Logger.get('webcast').error("""Calling the webcast synchronization URL: [%s] triggered Exception: %s""" % (str(url), str(e)))
                if raiseExceptionOnSyncFail:
                    raise e
        
        
        else:
            Logger.get('webcast').info("Webcast synchronization URL empty. We do not synchronize")
            return None
        
        
    
class HelperWebcastManager:
    """Helper class used for getting and instance of WebcastManager
        It will be migrated into a static method in WebcastManager class once the 
        ZODB4 is released and the Persistent classes are no longer Extension 
        ones.
    """
    
    def getWebcastManagerInstance(cls):
        dbmgr = DBMgr.getInstance()
        root = dbmgr.getDBConnection().root()        
        try:
            wm = root["WebcastManager"]
        except KeyError:
            wm = WebcastManager()
            root["WebcastManager"] = wm
        return wm
    
    getWebcastManagerInstance = classmethod( getWebcastManagerInstance )


class Channel(Persistent):
    """This class represents a live video channel: it has a unique name and
    a collection of video streams (one for each format supported by the channel
    """

    def __init__( self, name, url, width=480, height=360 ):
        self._name = name
        self._url = url
        self._width = width
        self._height = height
        self._onair = False
        self._onairEvent = None
        self._streams = []

    def setValues( self, name, url, width=480, height=360 ):
        self._name = name
        self._url = url
        self._width = width
        self._height = height
        
    def whatsOnAir( self ):
        try:
            return self._onairEvent
        except:
            self._onairEvent = None
            return None

    def isOnAir( self ):
        return self._onair

    def switchOnAir( self ):
        if self._onair:
            self._onair = False
        else:
            self._onair = True

    def setOnAir( self, event ):
        self._onairEvent = event

    def getName( self ):
        return self._name

    def getURL( self ):
        try:
            return self._url
        except:
            self._url = ""
            return ""
    
    def getStreams( self ):
        return self._streams

    def getStream( self, format ):
        for st in self._streams:
            if st.getFormat() == format:
                return st
        return None

    def getWidth( self ):
        try:
            return self._width
        except:
            self._width = 480
            return self._width

    def getHeight( self ):
        try:
            return self._height
        except:
            self._height = 360
            return self._height

    def addStream( self, format, url):
        if format != "" and not self.getStream(format):
            st = Stream( format, url )
            self._streams.append(st)
            self._p_changed=1

    def removeStream( self, format ):
        for st in self._streams:
            if st.getFormat() == format:
                self._streams.remove(st)
                self._p_changed=1

            
class Stream(Persistent):
    """This class represents a live video stream. Characteristics are the name
    of the stream format and the URL of the stream"""

    def __init__( self, format, url ):
        self._format = format
        self._url = url

    def getFormat( self ):
        return self._format

    def getURL( self ):
        return self._url

        
class Webcast(Persistent):
    """This class represents the live webcasts which may take place on some of the events
    """

    def __init__( self, event ):
        self._event = event
        self._id = event.getId()
        self._startDate = event.getStartDate()

    def getId( self ):
        return self._id

    def getEvent( self ):
        return self._event

    def getTitle( self ):
        return self._event.getTitle()

    def getStartDate( self ):
        return self._startDate

def sortWebcastByDate(x, y):
    return cmp(x.getStartDate(), y.getStartDate())

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

from MaKaC.webinterface.rh import base
from MaKaC.common import DBMgr, xmlGen
from MaKaC.common import indexes
from datetime import datetime
from MaKaC.errors import MaKaCError
from MaKaC import conference,webcast
from MaKaC.common.output import outputGenerator
from sets import Set

from MaKaC.user import LoginInfo
from MaKaC.authentication import AuthenticatorMgr
from MaKaC.user import AvatarHolder
from MaKaC.webinterface import webFactoryRegistry
from MaKaC.conference import CategoryManager,Conference
from MaKaC import user
from MaKaC.i18n import _
import MaKaC.common.info as info
from pytz import timezone

import MaKaC.webinterface.materialFactories as materialFactories
from MaKaC.webinterface import locators

class RHXMLHandlerBase ( base.RH ):

    def _genStatus (self, statusValue, message, XG):
        XG.openTag("status")
        XG.writeTag("value", statusValue)
        XG.writeTag("message", message)
        XG.closeTag("status")

    def _createResponse (self, statusValue, message):
        XG = xmlGen.XMLGen()
        XG.openTag("response")
        self._genStatus(statusValue, message, XG)
        XG.closeTag("response")

        self._req.content_type = "text/xml"
        return XG.getXml()


class RHLoginStatus( RHXMLHandlerBase ):
    def _process( self ):
        XG = xmlGen.XMLGen()
        XG.openTag("response")
        self._genStatus("OK", "Request succesful", XG)
        XG.openTag("login-status")
        if self._getSession().getUser() != None:
            XG.writeTag("user-id", self._getSession().getUser().getId())
        XG.closeTag("login-status")
        XG.closeTag("response")
        
        self._req.content_type = "text/xml"
        return XG.getXml()
        

class RHSignIn( RHXMLHandlerBase ):
    
    def _checkParams( self, params ):
        
        self._login = params.get( "login", "" ).strip()
        self._password = params.get( "password", "" ).strip()
    
    def _process( self ):

        li = LoginInfo( self._login, self._password )   
        auth = AuthenticatorMgr()
        av = auth.getAvatar(li)
        value = "OK"
        message = ""
        if not av:
            value = "ERROR"
            message = "Login failed"
        elif not av.isActivated():
            if av.isDisabled():
                value = "ERROR"
                message = "Acount is disabled"
            else:
                value = "ERROR"
                message = "Acount is not activated"
        else:
            value = "OK"
            message = "Login succesful"
            self._getSession().setUser( av )

        return self._createResponse(value, message)


class RHSignOut( RHXMLHandlerBase ):
    
    def _process( self ):
        if self._getUser():
            self._getSession().setUser( None )
            self._setUser( None )

        return self._createResponse("OK", "Logged out")

class RHWebcastOnAir( RHXMLHandlerBase ):

    def _printWebcast(self, wc, XG):
        XG.openTag("webcast")
        XG.writeTag("title",wc.getTitle())
        XG.writeTag("startDate",wc.getStartDate())
        XG.writeTag("id",wc.getId())
        XG.closeTag("webcast")

    def _printStream( self, stream, XG ):
        XG.openTag("stream")
        XG.writeTag("format",stream.getFormat())
        XG.writeTag("url",stream.getURL())
        XG.closeTag("stream")

    def _printChannel(self, ch, XG):
        XG.openTag("channel")
        XG.writeTag("name",ch.getName())
        XG.writeTag("width",ch.getWidth())
        XG.writeTag("height",ch.getHeight())
        if ch.isOnAir():
            XG.writeTag("onair","True")
        for stream in ch.getStreams():
            self._printStream(stream,XG)
        wc = ch.whatsOnAir()
        if wc:
            self._printWebcast(wc,XG)
        XG.closeTag("channel")

    def _process( self ):
        wm = webcast.HelperWebcastManager.getWebcastManagerInstance()
        XG = xmlGen.XMLGen()
        XG.openTag("response")
        XG.openTag("status")
        XG.writeTag("value", "OK")
        XG.writeTag("message", "Returning on air events on all channels")
        XG.closeTag("status")
        XG.openTag("channels")
        for ch in wm.getChannels():
            self._printChannel(ch,XG)
        XG.closeTag("channels")
        XG.closeTag("response")
        self._req.content_type = "text/xml"
        return XG.getXml()

class RHWebcastForthcomingEvents( RHXMLHandlerBase ):

    def _printWebcast(self, wc, XG):
        XG.openTag("webcast")
        XG.writeTag("title",wc.getTitle())
        XG.writeTag("id",wc.getId())
        XG.writeTag("startDate",wc.getStartDate())
        XG.closeTag("webcast")
        
    def _process( self ):
        wm = webcast.HelperWebcastManager.getWebcastManagerInstance()
        XG = xmlGen.XMLGen()
        XG.openTag("response")
        XG.openTag("status")
        XG.writeTag("value", "OK")
        XG.writeTag("message", "Returning all forthcoming webcasts")
        XG.closeTag("status")
        XG.openTag("webcasts")
        webcasts = wm.getForthcomingWebcasts()
        webcasts.sort(webcast.sortWebcastByDate)
        for wc in webcasts:
            if not wc in wm.whatsOnAir():
                self._printWebcast(wc,XG)
        XG.closeTag("webcasts")
        XG.closeTag("response")
        self._req.content_type = "text/xml"
        return XG.getXml()
    
class RHSearch ( base.RHProtected, RHXMLHandlerBase ):

  def _stringToDatetime(self, source):
    """This method expects dates in the form "yyyy-mm-dd hh:mm" """

    return datetime(int(source[0:4]), int(source[5:7]), int(source[8:10]), \
      int(source[11:13]), int(source[14:16]),tzinfo=timezone(info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()))

  def _extractParam(self, params, paramName, attrName = None):

    if (attrName == None):
      attrName = "_" + paramName

    if (params.has_key(paramName)):
      setattr(self, attrName, params[paramName])
      return True
    else:
      setattr(self, attrName, None)
      return False

  def _extractDateParam(self, params, paramName, attrName = None):

    if (attrName == None):
      attrName = "_" + paramName
    try:    
      if (self._extractParam(params, paramName, attrName)):
        setattr(self, attrName, self._stringToDatetime(getattr(self, attrName)))
    except:
      raise MaKaCError( _("Invalid date format"))

  def _checkAuthor(self, conf, name):
    # This checks whether an author is involved in a conference
    idx1 = conf.getAuthorIndex()
    idx2 = conf.getSpeakerIndex()
    if idx1.match({"name": name}) or \
      idx1.match({"surName": name}) or \
      idx2.match({"name": name}) or \
      idx2.match({"surName": name}):
      return True
    else:
      return False

  def _checkRoom(self, conf, room):
    if conf.getRoom() != None and conf.getRoom().getName().lower().find(room.lower()) != -1:
      return True
    for i in conf.getSessionList():
      if i.getRoom() != None and i.getRoom().getName().lower().find(room.lower()) != -1:
        return True
    for i in conf.getContributionList():
      if i.getRoom() != None and i.getRoom().getName().lower().find(room.lower()) != -1:
        return True
      for j in i.getSubContributionList():
        if j.getRoom() != None and j.getRoom().getName().lower().find(room.lower()) != -1:
          return True
    return False
      
    

  def _checkParams(self, params):
    base.RHProtected._checkParams(self, params)

    self._statusValue = "OK"
    self._message = ""

    try:
      # extract interesting parameters from request
      dateParams = [ "startDateAt", "endDateAt", "startDateFrom", \
        "startDateTo", "endDateFrom", "endDateTo", "date" ]
      otherParams = [ "category", "room", "id", "author", "format" ]
      for i in dateParams:
        self._extractDateParam(params, i)
      for i in otherParams:
        self._extractParam(params, i)

      # sanity checks
      # range boundaries must be given together
      if (self._startDateFrom != None) != (self._startDateTo != None):
        raise MaKaCError( _("Incomplete range"))
      if (self._endDateFrom != None) != (self._endDateTo != None):
        raise MaKaCError( _("Incomplete range"))

      # ensure that ranges are constructed correctly
      if self._startDateFrom != None and \
        self._startDateFrom >= self._startDateTo:
        raise MaKaCError( _("startDateTo must be greater than startDateFrom"))
      if self._endDateFrom != None and \
        self._endDateFrom >= self._endDateTo:
        raise MaKaCError( _("endDateTo must be greater than endDateFrom"))

      # dates must be specified either precisely or by a range, but not both
      if self._startDateFrom != None and self._startDateAt != None:
        raise MaKaCError( _("Use either startDateFrom/startDateTo or startDateAt"))
      if self._endDateFrom != None and self._endDateAt != None:
        raise MaKaCError( _("Use either endDateFrom/endDateTo or endDateAt"))

      # At least one date or one range of dates should be specified
      if self._startDateFrom == None and self._startDateAt == None and \
        self._endDateFrom == None and self._endDateAt == None and self._id == None and self._date == None:
        raise MaKaCError( _("At least one date/range of dates or a conference id must be specified"))
    except MaKaCError, e:
      self._statusValue = "ERROR"
      self._message = e.getMsg()
    except:
      self._statusValue = "ERROR"
      self._message = "Internal error"

  def _printSubContribution(self, s, XG):
    if s.canAccess(self.getAW()):
      XG.openTag("subcontribution")
      XG.writeTag("id", s.getId())
      XG.writeTag("title", s.getTitle())
      XG.writeTag("startDate", s.getContribution().getStartDate())
      XG.writeTag("timezone", 'UTC')
      if s.getRoom() != None:
        XG.writeTag("room", s.getRoom().getName())
      else:
        XG.writeTag("room", "")
      XG.closeTag("subcontribution")

  def _printContribution(self, c, XG):
    if c.canAccess(self.getAW()):
      XG.openTag("contribution")
      XG.writeTag("id", c.getId())
      XG.writeTag("title", c.getTitle())
      XG.writeTag("startDate", c.getStartDate())
      XG.writeTag("endDate", c.getEndDate())
      XG.writeTag("timezone", 'UTC')
      if c.getRoom() != None:
        XG.writeTag("room", c.getRoom().getName())
      else:
        XG.writeTag("room", "")
      for i in c.getSubContributionList():
        self._printSubContribution(i, XG)
      XG.closeTag("contribution")

  def _printSession(self, s, XG):
    if s.canAccess(self.getAW()):
      XG.openTag("session")
      XG.writeTag("id", s.getId())
      XG.writeTag("title", s.getTitle())
      XG.writeTag("startDate", s.getStartDate())
      XG.writeTag("endDate", s.getEndDate())
      XG.writeTag("timezone", 'UTC')
      if s.getRoom() != None:
        XG.writeTag("room", s.getRoom().getName())
      else:
        XG.writeTag("room", "")
      for i in s.getContributionList():
        if i.isScheduled():
          self._printContribution(i, XG)
      XG.closeTag("session")

  def _printConference(self, c, XG):
    if c.canAccess(self.getAW()):
      XG.openTag("event")
      XG.writeTag("id", c.getId())
      XG.writeTag("title", c.getTitle())
      XG.writeTag("startDate", c.getStartDate())
      XG.writeTag("endDate", c.getEndDate())
      XG.writeTag("timezone", 'UTC')
      XG.writeTag("eventTimezone", c.getTimezone())
      if c.getRoom() != None:
        XG.writeTag("room", c.getRoom().getName())
      else:
        XG.writeTag("room", "")
      for i in c.getChairList():
        XG.writeTag("chairman", i.getFullName())
      if c.getChairmanText() != "":
        XG.writeTag("chairmanText", c.getChairmanText())
      for i in c.getSessionListSorted():
        if self._dateFit(i):
          self._printSession(i, XG)
      for i in c.getContributionList():
        # list only 'orphaned' contributions
        if i.getSession() == None:
          if i.isScheduled() and self._dateFit(i):
            self._printContribution(i, XG)
      XG.closeTag("event")

  def _dateFit(self, item):
    if self._date != None:
      if item.getStartDate().date() <= self._date.date() and item.getEndDate().date() >= self._date.date():
        return True
      else:
        return False
    return True

  def _process(self):
    if self._statusValue != "OK":
      return self._createResponse(self._statusValue, self._message)

    ih = indexes.IndexesHolder()
    calIdx = ih.getIndex("calendar")
    catIdx = ih.getIndex("category")
    ch = conference.ConferenceHolder()

    # A *preliminary* set of conference id's is created here
    # This set is constructed using indexes, without getting the Conference
    # objects from the DB.
 
    listOfSets = []

    if self._startDateAt != None:
      listOfSets.append(calIdx.getObjectsStartingInDay(self._startDateAt))

    if self._startDateFrom != None:
      listOfSets.append(calIdx.getObjectsStartingIn(self._startDateFrom,self._startDateTo))

    if self._endDateAt != None:
      listOfSets.append(calIdx.getObjectsEndingInDay(self._endDateAt))

    if self._endDateFrom != None:
      listOfSets.append(calIdx.getObjectsEndingIn(self._endDateFrom,self._endDateTo))

    if self._date != None:
      listOfSets.append(calIdx.getObjectsIn(self._date, self._date))

    if self._category != None:
      resultSet = Set()
      if type(self._category) is list:
        for i in self._category:
          resultSet.union_update(catIdx.getItems(i))
      else:
        resultSet.union_update(catIdx.getItems(self._category))

      listOfSets.append(resultSet)

    if self._id != None:
      resultSet = Set()
      if type(self._id) is list:
        listOfSets.append(Set(self._id))
      else:
        listOfSets.append(Set([self._id]))

    prelimResult = listOfSets[0]
    for i in range(1, len(listOfSets)):
      prelimResult.intersection_update(listOfSets[i])

    result = Set()

    XG = xmlGen.XMLGen()
    XG.openTag("response")
    XG.openTag("status")
    XG.writeTag("value", "OK")
    XG.writeTag("message", "Returning search results")
    XG.closeTag("status")
    XG.openTag("event-list")
    for i in prelimResult:
      try:
        try:
            c = ch.getById(i)
        except:
            continue
        if self._author != None and not self._checkAuthor(c, self._author):
          continue
        if self._room != None and not self._checkRoom(c, self._room):
          continue
        if self._startDateFrom != None:
          if c.getStartDate() < self._startDateFrom or \
            c.getStartDate() > self._startDateTo:
            continue
        if self._startDateAt != None:
          if c.getStartDate() != self._startDateAt:
            continue
        if self._endDateFrom != None:
          if c.getEndDate() < self._endDateFrom or \
            c.getEndDate() > self._endDateTo:
              continue
        if self._endDateAt != None:
          if c.getEndDate() != self._endDateAt:
            continue
        result.add(i)
        if self._format != "full":
            self._printConference(c, XG)
        else:
            XG.openTag("event")
            og = outputGenerator(self.getAW(), XG)
            og._confToXML(c,{})
            XG.closeTag("event")
            
      except KeyError:
        continue

    XG.closeTag("event-list")
    XG.closeTag("response")
    self._req.content_type = "text/xml"

    return XG.getXml()
    
class RHAddMaterialBase ( base.RHModificationBaseProtected, RHXMLHandlerBase ):

    def _checkParams(self, params):
        base.RHModificationBaseProtected._checkParams(self, params)
        self._title = params.get('title', 'video')
        self._value = params.get('value', '')
        
    def _process(self):
        try:
            try:
                m = self._target.getMaterialById(self._title)
            except:
                m = None
            if m == None:
                m = conference.Material()
                self._target.addMaterial( m )
                params = { "title":self._title }
                m.setValues(params)
            l = conference.Link()
            l.setURL(self._value)
            m.addResource(l)
            m.setMainResource(l)
        except MaKaCError, e:
            return self._createResponse("ERROR", e.getMsg())
        except Exception, e:
            return self._createResponse("ERROR", "internal error: %s" % e)
        return self._createResponse("OK", "Material added")

class RHAddMaterialToConference (RHAddMaterialBase):

    def _checkParams(self, params):
        l = locators.WebLocator()
        l.setConference( params )
        self._target = l.getObject()
        RHAddMaterialBase._checkParams(self, params)

class RHAddMaterialToSession (RHAddMaterialBase):

    def _checkParams(self, params):
        l = locators.WebLocator()
        l.setSession( params )
        self._target = l.getObject()
        RHAddMaterialBase._checkParams(self, params)

class RHAddMaterialToContribution (RHAddMaterialBase):

    def _checkParams(self, params):
        l = locators.WebLocator()
        l.setContribution( params )
        self._target = l.getObject()
        RHAddMaterialBase._checkParams(self, params)

class RHAddMaterialToSubContribution (RHAddMaterialBase):

    def _checkParams(self, params):
        l = locators.WebLocator()
        l.setSubContribution( params )
        self._target = l.getObject()
        RHAddMaterialBase._checkParams(self, params)

class RHCreateEventBase ( base.RHProtected, RHXMLHandlerBase ):

    def _checkParams(self, params):

        base.RHProtected._checkParams(self, params)
        self._statusValue = "OK"
        self._message = ""
        try:
            self._title = params.get( "title", "" ).strip()
            self._startdate = params.get( "startdate", "" ).strip()
            self._enddate = params.get( "enddate", "" ).strip()
            self._place = params.get( "place", "" ).strip()
            self._room = params.get( "room", "" ).strip()
            self._accessPassword = params.get( "an", "" ).strip()
            self._modifyPassword = params.get( "mp", "" ).strip()
            self._style = params.get( "style", "" ).strip()
            self._fid = params.get( "fid", "" ).strip()
            self._description = params.get( "description", "" ).strip()
            self._stime = params.get( "stime", "" ).strip()
            self._etime = params.get( "etime", "" ).strip()
            self._speaker = params.get( "speaker", "" ).strip()
            self._speakeremail = params.get( "email", "" ).strip()
            self._speakeraffiliation = params.get( "affiliation", "" ).strip()
            if not self._title or not self._startdate or not self._enddate or not self._fid or not self._stime or not self._etime:
                raise MaKaCError( _("mandatory parameter missing"))
            ch = CategoryManager()
            try:
                self._cat = ch.getById(self._fid)
            except:
                raise MaKaCError( _("unknown category"))
        except MaKaCError, e:
          self._statusValue = "ERROR"
          self._message = e.getMsg()
        except:
          self._statusValue = "ERROR"
          self._message = "Internal error"

    def _process(self):
        try:
            ah = user.AvatarHolder()
            us = ah.match({'email':'cds.support@cern.ch'})[0]
            self._event = self._cat.newConference(us)
            self._event.setTitle(self._title)
            self._event.setDescription(self._description)
            sd = self._startdate.split("/")
            st = self._stime.split(":")
            sdate = datetime(int(sd[2]),int(sd[1]),int(sd[0]),int(st[0]),int(st[1]))
            ed = self._enddate.split("/")
            et = self._etime.split(":")
            edate = datetime(int(ed[2]),int(ed[1]),int(ed[0]),int(et[0]),int(et[1]))
            self._event.setDates(sdate,edate)
            chair = conference.ConferenceChair()
            chair.setFamilyName(self._speaker)
            chair.setEmail(self._speakeremail)
            self._event.addChair(chair)
            self._event.setAccessKey(self._accessPassword)
            self._event.setModifKey(self._modifyPassword)
        except MaKaCError, e:
            self._statusValue = "ERROR"
            self._message = e.getMsg()
        except:
            self._statusValue = "ERROR"
            self._message = "Internal error"

        
class RHCreateLecture ( RHCreateEventBase ):

    def _process(self):
        if self._statusValue != "OK":
          return self._createResponse(self._statusValue, self._message)
        RHCreateEventBase._process( self )
        if self._statusValue != "OK":
          return self._createResponse(self._statusValue, self._message)
        wr = webFactoryRegistry.WebFactoryRegistry()
        fact = wr.getFactoryById('simple_event')
        wr.registerFactory(self._event, fact)
        return self._createResponse("OK", "Lecture %s added" % self._event.getId())


class RHCategInfo( RHXMLHandlerBase ):
    
    def _checkParams( self, params ):
        self._id = params.get( "id", "" ).strip()
        self._fp = params.get( "fp", "no" ).strip()

    def _getHeader( self, XG ):
        XG.openTag("response")
        XG.openTag("status")
        XG.writeTag("value", "OK")
        XG.writeTag("message", "Returning category info")
        XG.closeTag("status")

    def _getFooter( self, XG ):
        XG.closeTag("response")

    def _getCategXML( self, cat, XG, fp="no" ):
        XG.openTag("categInfo")
        XG.writeTag("title",cat.getTitle())
        XG.writeTag("id",cat.getId())
        if fp == "yes":
            XG.openTag("father")
            if cat.getOwner():
                self._getCategXML(cat.getOwner(),XG,fp)
                fatherid = cat.getOwner().getId()
            XG.closeTag("father")
        XG.closeTag("categInfo")
        return XG.getXml()

    def _process( self ):
        self._req.content_type = "text/xml"
        cm = CategoryManager()
        try:
            XG = xmlGen.XMLGen()
            cat = cm.getById(self._id)
            self._getHeader(XG)
            self._getCategXML(cat, XG, self._fp)
            self._getFooter(XG)
            return XG.getXml()
        except:
            value = "ERROR"
            message = "Category does not exist"
        if value != "OK":
            return self._createResponse(value, message)


class RHStatsRoomBooking( base.RoomBookingDBMixin, RHXMLHandlerBase ):

    def _createIndicator( self, XG, name, fullname, value ):
        XG.openTag("indicator")
        XG.writeTag("name", name)
        XG.writeTag("fullname", fullname)
        XG.writeTag("value", value)
        XG.closeTag("indicator")
        
    def _process( self ):
        from MaKaC.rb_room import RoomBase
        from datetime import datetime,timedelta
        from MaKaC.rb_reservation import ReservationBase

        startdt = enddt = datetime.now()
        today = startdt.date()
        startdt.replace( hour = 0, minute = 0)
        enddt.replace( hour = 23, minute = 59)
        
        self._req.content_type = "text/xml"
        XG = xmlGen.XMLGen()
        XG.openTag("response")
        
        rooms = RoomBase.getRooms()
        nbRooms = len(rooms)
        nbPublicRooms = nbPrivateRooms = nbSemiPrivateRooms = 0
        for r in rooms:
            if not r.isReservable:
                nbPrivateRooms += 1
            elif not r.resvsNeedConfirmation:
                nbPublicRooms += 1
            else:
                nbSemiPrivateRooms += 1
                
        self._createIndicator(XG, "total", "total number of managed rooms", nbRooms)
        self._createIndicator(XG, "public", "number of public rooms", nbPublicRooms)
        self._createIndicator(XG, "semiprivate", "number of semi-private rooms", nbSemiPrivateRooms)
        self._createIndicator(XG, "private", "number of private rooms", nbPrivateRooms)

        resvex = ReservationBase()
        resvex.isConfirmed = True
        resvex.isCancelled = False
        nbResvs = len(ReservationBase.getReservations( resvExample = resvex, days = [ startdt.date() ] ))
        resvex.usesAVC = True
        nbAVResvs = len(ReservationBase.getReservations( resvExample = resvex, days = [ startdt.date() ] ))
        resvex.needsAVCSupport = True
        nbAVResvsWithSupport = len(ReservationBase.getReservations( resvExample = resvex, days = [ startdt.date() ] ))
        
        self._createIndicator(XG, "nbbookings", "total number of bookings for today", nbResvs)
        self._createIndicator(XG, "nbvc", "number of remote collaboration bookings (video or phone conference)", nbAVResvs)
        self._createIndicator(XG, "nbvcsupport", "number of remote collaboration bookings with planned IT support", nbAVResvsWithSupport)
        
        XG.closeTag("response")
        return XG.getXml()


class RHStatsIndico( RHXMLHandlerBase ):

    def _createIndicator( self, XG, name, fullname, value ):
        XG.openTag("indicator")
        XG.writeTag("name", name)
        XG.writeTag("fullname", fullname)
        XG.writeTag("value", value)
        XG.closeTag("indicator")
        
    def _process( self ):
        from datetime import datetime,timedelta
        from MaKaC.common.indexes import IndexesHolder

        self._req.content_type = "text/xml"
        XG = xmlGen.XMLGen()
        XG.openTag("response")
        
        now = startdt = enddt = datetime.now()
        today = startdt.date()
        startdt.replace( hour = 0, minute = 0)
        enddt.replace( hour = 23, minute = 59)

        calIdx = IndexesHolder().getById("calendar")

        nbEvtsToday = len(calIdx.getObjectsInDay(now))
        nbOngoingEvts = len(calIdx.getObjectsIn(now,now))

        self._createIndicator(XG, "nbEventsToday", "total number of events for today", nbEvtsToday)
        self._createIndicator(XG, "nbOngoingEvents", "total number of ongoing events", nbOngoingEvts)
        XG.closeTag("response")
        return XG.getXml()

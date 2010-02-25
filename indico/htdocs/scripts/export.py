# -*- coding: utf-8 -*-
##
## $Id: export.py,v 1.10 2008/08/13 13:31:19 jose Exp $
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

import sys,re
import datetime,sets

from MaKaC.common.general import *
from MaKaC.common import db
from MaKaC.conference import ConferenceHolder,CategoryManager
from MaKaC.common import indexes
from MaKaC.common import xmlGen
from MaKaC.webinterface.urlHandlers import UHMaterialDisplay
from MaKaC.ICALinterface.conference import ConferenceToiCal
from MaKaC.ICALinterface.base import ICALBase
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.common.Configuration import Config
from MaKaC.webinterface import urlHandlers
import MaKaC.common.info as info
from MaKaC.common.timezoneUtils import nowutc
from pytz import timezone
from pytz import all_timezones

def index(req, **params):
  """This script displays the list of meetings taking place in a given category
  at a given date"""
  global ids
  db.DBMgr.getInstance().startRequest()
  try:
    fid = params['fid']
    date = params['date']
    days = int(params['days'])-1
    event = params.get('event',"")
    of = params.get('of','text')
    rooms = params.get('rooms',[])
    tzstring = params.get('tz',info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone())
    if tzstring not in all_timezones:
        tzstring = 'UTC'
    tz = timezone(tzstring)
    protected = int(params.get('protected',1))
    # repeat the event every day of its duration
    repeat = int(params.get('re',0))
    # display the category tree the event belongs to
    displayCateg = int(params.get('dc',1))
  except:
    return usage()
  #instanciate indexes
  #create list of ids
  ids = re.split(' ',fid)
  event_types = re.split(' ',event)
  #create date object
  if date == "today":
    date = nowutc().astimezone(tz).date().isoformat()
  [year, month, day] = re.split('-',date)
  startdate = tz.localize(datetime.datetime(int(year),int(month),int(day),0,0,0))
  enddate   = startdate + datetime.timedelta(days=days,hours=23,minutes=59,seconds=59)
  res = getConfList(startdate,enddate,ids)
  # filter with event type
  if event_types != ['']:
    finalres = []
    ch = ConferenceHolder()
    for confId in res:
      conf = ch.getById(confId)
      type = conf.getType()
      if type in event_types:
        finalres.append(confId)
  else:
    finalres = res
  res = finalres
  # filter with room name
  if rooms != []:
    finalres = []
    ch = ConferenceHolder()
    for confId in res:
      conf = ch.getById(confId)
      if conf.getRoom():
        confroom = conf.getRoom().getName()
        if confroom in rooms:
          finalres.append(confId)
  else:
    finalres = res
  # filter protected events
  ch = ConferenceHolder()
  if not protected:
    for id in finalres:
      conf = ch.getById(id)
      if conf.isProtected():
        finalres.remove(id)
  if of=='xml':
    req.content_type="text/xml"
    return displayXMLList(finalres, req, tzstring, displayCateg)
  elif of=='rss':
    req.content_type="application/xhtml+xml"
    return displayRSSList(finalres, req, tzstring)
  elif of=='ical':
    req.content_type="text/v-calendar"
    return displayICalList(finalres, req)
  else:
    req.content_type="text/html"
    return displayList(finalres,startdate,enddate,repeat,displayCateg, tzstring)

def usage():
  return """usage: export.py?fid=xxx&date=yyyy-mm-dd&days=xxx&of=yyy&re=r&dc=d&event=e&tz=tz

fid: id of the category in which to search the events
date: date on which to start the search
days: number of days on which to span the search
of: output format (one of xml, ical, rss or html)
re: repeat event on all the days it spans over (html only)
dc: display father category names (0, 1 or 2)
event: type of the event (conference, meeting or simple_event)
rooms: repeating field to filter on room names
tz: timezone name or absent for default server timezone"""

def displayICalList(res,req):
  filename = "Event.ics"

  # TODO: proper methods in the iCal interface
  # for serializing a sequence of events

  icalBase = ICALBase()
  data = icalBase._printHeader()

  ch = ConferenceHolder()
  for confId in res:
    conf = ch.getById(confId)
    ical = ConferenceToiCal(conf.getConference())
    data += ical.getCore()
  data += icalBase._printFooter()
  req.headers_out["Content-Length"] = "%s"%len(data)
  cfg = Config.getInstance()
  mimetype = cfg.getFileTypeMimeType( "ICAL" )
  req.content_type = """%s"""%(mimetype)
  req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
  return data

def displayList(res,startdate,enddate,repeat,displayCateg,tz):
  text = ""
  ch = ConferenceHolder()
  day = startdate
  days = {}
  found = {}
  while day <= enddate:
    for confId in res:
      c = ch.getById(confId)
      if day.date() >= c.getAdjustedStartDate(tz).date() and day.date() <= c.getAdjustedEndDate(tz).date() and (repeat==1 or not found.has_key(c)):
        if not days.has_key(day):
	  days[day]=[]
        days[day].append(c)
	found[c] = 1
    day = day + datetime.timedelta(days=1)
  day = startdate
  while day <= enddate:
    if days.has_key(day):
      text += "<br><b>%s</b>" % day.strftime("%A %B %d, %Y")
      days[day].sort(lambda x,y: cmp(x.calculateDayStartTime(day).time(),y.calculateDayStartTime(day).time()))
      for c in days[day]:
        text += displayConf(c,displayCateg,day,tz)
    day = day + datetime.timedelta(days=1)
  return text

def displayConf(conf,displayCateg,day,tz):
  if conf.getRoom() != None:
    room = conf.getRoom().getName()
  else:
    room = ""
  categText = getCategText(conf.getOwnerList()[0], displayCateg)
  if day:
    startTime = conf.calculateDayStartTime(day).time().isoformat()[0:5]
  else:
    startTime = conf.getAdjustedStartDate(tz).time().isoformat()[0:5]
  if Config.getInstance().getShortEventURL() != "":
    url = "%s%s" % (Config.getInstance().getShortEventURL(),conf.getId())
  else:
    url = urlHandlers.UHConferenceDisplay.getURL( conf )
  speakers = ""
  for chair in conf.getChairList():
    if speakers != "":
      speakers += ", "
    speakers += chair.getDirectFullName()
    if chair.getAffiliation() != "":
      speakers += " (%s)" % chair.getAffiliation()
  t = "<br><b>%s</b>%s&nbsp;/&nbsp;<a href=\"%s\">%s</a>/%s/%s" % (startTime,categText,url,conf.getTitle(),speakers,room)
  return t

def displayXMLList(res, req, tz, dc=1):
  ch = ConferenceHolder()
  xml = xmlGen.XMLGen()
  xml.openTag("collection")
  for confId in res:
    c = ch.getById(confId)
    xml = displayXMLConf(c,xml,tz,dc)
  xml.closeTag("collection")
  return xml.getXml()

def displayXMLConf(conf,xml,tz,dc=1):
  xml.openTag("agenda_item")
  xml.writeTag("id",conf.getId())
  xml.writeTag("agenda_url",urlHandlers.UHConferenceDisplay.getURL( conf ))
  xml.writeTag("category",getCategText(conf.getOwnerList()[0],dc))
  xml.writeTag("title",conf.getTitle())
  for chair in conf.getChairList():
    xml.writeTag("speaker",chair.getFullName())
    if chair.getAffiliation() != "":
       xml.writeTag("affiliation",chair.getAffiliation())
  xml.writeTag("start_date",conf.getAdjustedStartDate(tz).date().isoformat())
  xml.writeTag("start_time",conf.getAdjustedStartDate(tz).time().isoformat()[0:5])
  xml.writeTag("end_date",conf.getAdjustedEndDate(tz).date().isoformat())
  xml.writeTag("end_time",conf.getAdjustedEndDate(tz).time().isoformat()[0:5])
  if conf.getRoom():
    room = conf.getRoom().getName()
    xml.writeTag("room",room)
  else:
    room=""
  if room.find('-') != -1:
    building = room[0:room.find('-')]
  else:
    building = room.replace(' ','+')
  if building != '':
    xml.writeTag("building",building)
  mats = conf.getMaterialList()
  for mat in mats:
    xml.openTag("filedir")
    xml.writeTag("filedir_description", mat.getTitle())
    xml.writeTag("filedir_url", str(UHMaterialDisplay.getURL(mat)))
    xml.closeTag("filedir")
  xml.closeTag("agenda_item")
  return xml

def getCategText(categ,dc=1):
  global ids
  if categ == None or dc == 0:
    return ""
  if categ.getId() in ids or dc == 2:
    return categ.getName()
  else:
    return "%s&nbsp;/&nbsp;%s" % (getCategText(categ.getOwner()),categ.getName())

def displayRSSList(res,req,tz):
  ch = ConferenceHolder()
  rss = xmlGen.XMLGen()
  rss.openTag('rss version="2.0"')
  rss.openTag("channel")
  rss.writeTag("title","Indico RSS Feed")
  rss.writeTag("link", Config.getInstance().getBaseURL())
  rss.writeTag("description","Export of some events stored in Indico")
  rss.writeTag("language","en")
  rss.writeTag("pubDate", nowutc().strftime("%a, %d %b %Y %H:%M:%S %Z"))
  rss.writeTag("category","")
  rss.writeTag("generator", "CDS Indico %s" % Config.getInstance().getVersion())
  rss.writeTag("webMaster", HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail())
  rss.writeTag("ttl","1440")
  for confId in res:
    c = ch.getById(confId)
    rss = displayRSSConf(c,rss,tz)
  rss.closeTag("channel")
  rss.closeTag("rss")
  return rss.getXml()

def displayRSSConf(conf,rss,tz):
  date = str(conf.getAdjustedStartDate(tz).date().isoformat())
  time = str(conf.getAdjustedStartDate(tz).time().isoformat()[0:5])
  title = "%s - %s - %s" % (date, time, conf.getTitle())
  if Config.getInstance().getShortEventURL() != "":
    url = "%s%s" % (Config.getInstance().getShortEventURL(),conf.getId())
  else:
    url = urlHandlers.UHConferenceDisplay.getURL( conf )
  rss.openTag("item")
  rss.writeTag("title", title )
  rss.writeTag("link",url)
  if conf.isProtected():
    desc = getCategText(conf.getOwnerList()[0])
  else:
    desc = "%s<br>%s" % (getCategText(conf.getOwnerList()[0]),conf.getDescription())
  rss.writeTag("description", desc )
  rss.writeTag("pubDate", conf.getModificationDate().strftime("%a, %d %b %Y %H:%M:%S %Z"))
  rss.writeTag("guid",url)
  rss.closeTag("item")
  return rss

def sortByStartDate(conf1,conf2):
  ch = ConferenceHolder()
  return cmp(ch.getById(conf1).getStartDate(),ch.getById(conf2).getStartDate())

def getConfList(startdate,enddate,ids):
  #create result set
  res = sets.Set()
  #instanciate indexes
  im = indexes.IndexesHolder()
  catIdx = im.getIndex('category')
  calIdx = im.getIndex('calendar')
  c1 = calIdx.getObjectsIn(startdate, enddate)
  for id in ids:
    confIds=sets.Set(catIdx.getItems(id))
    confIds.intersection_update(c1)
    res.union_update(confIds)
  res = list(res)
  res.sort(sortByStartDate)
  return res

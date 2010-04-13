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

import sys,re
import sets

from MaKaC.common.general import *
from MaKaC.common import db
from MaKaC.conference import ConferenceHolder,CategoryManager
from MaKaC.common import indexes
from MaKaC.common.timezoneUtils import nowutc
import MaKaC.common.info as info
from pytz import timezone

def index(req, **params):
  """This script displays the list of meetings which are planned in the coming
  week"""
  global ids
  db.DBMgr.getInstance().startRequest()

  #create list of ids
  ids = ['1l7']
  tz = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
  #create date object
  startdate = nowutc()
  #create result set
  res = getConfList(startdate,ids)
  req.content_type="text/html"
  return displayList(res,tz)

def displayList(res,tz):
  text = """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<HTML>
<HEAD>
   <TITLE>Forthcoming Seminars</TITLE>
   <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
</HEAD>
<BODY LINK="#0000FF" VLINK="#800080">

<H1>
<A HREF="http://www.cern.ch/"><IMG SRC="http://www.cern.ch/CommonImages/Banners/CERNHeadE.gif" ALT="CERN European Laboratory for Particle Physics" NOSAVE BORDER=0 HEIGHT=20 WIDTH=411></A></H1>

<H2>
FORTHCOMING SEMINARS / SEMINAIRES A VENIR</H2>
"""
  ch = ConferenceHolder()
  curDate = None
  for confId in res:
    c = ch.getById(confId)
    if curDate!=c.getAdjustedStartDate(tz):
      curDate = c.getAdjustedStartDate(tz)
      text += "<hr>%s<br>" % curDate.strftime("%A %B %d, %Y")
    text += displayConf(c,tz)
  return text

def displayConf(conf,tz):
  if conf.getRoom() != None:
    room = conf.getRoom().getName()
  else:
    room = ""
  t = "<b>%s</b>&nbsp;/&nbsp;%s&nbsp;/&nbsp;<a href=\"http://indico.cern.ch/conferenceDisplay.py?confId=%s\">%s</a>/%s" % (conf.getAdjustedStartDate(tz).time().isoformat()[0:5],conf.getOwnerList()[0].getName(),conf.getId(),conf.getTitle(),room)
  return t


def sortByStartDate(conf1,conf2):
  ch = ConferenceHolder()
  return cmp(ch.getById(conf1).getStartDate(),ch.getById(conf2).getStartDate())

def getConfList(startdate,ids):
  #create result set
  res = sets.Set()
  #instanciate indexes
  im = indexes.IndexesHolder()
  catIdx = im.getIndex('category')
  calIdx = im.getIndex('calendar')
  c1 = calIdx.getObjectsStartingAfter(startdate)
  for id in ids:
    confIds=sets.Set(catIdx.getItems(id))
    confIds.intersection_update(c1)
    res.union_update(confIds)
  res = list(res)
  res.sort(sortByStartDate)
  return res

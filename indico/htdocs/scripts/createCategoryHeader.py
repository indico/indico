# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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

import sys,re
import datetime,sets

from MaKaC.common.general import *
from MaKaC.common import db
from MaKaC.conference import CategoryManager
from MaKaC.common import indexes
import MaKaC.common.info as info
from MaKaC.common.timezoneUtils import nowutc
from pytz import timezone


def index(req, **params):
  """This script displays the list of meetings taking place in a given category
  at a given date"""
  global ids
  try:
    fid = params['fid']
    date = params['date']
  except:
    return usage()

  #create list of ids
  ids = re.split(' ',fid)
  #create date object
  db.DBMgr.getInstance().startRequest()
  tz = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
  [year, month, day] = re.split('-',date)
  startdate = timezone(tz).localize(datetime.datetime(int(year),int(month),int(day)))
  enddate   = startdate.replace(hour=23,minute=59)
  #create result set
  res = sets.Set()

  #instanciate indexes
  im = indexes.IndexesHolder()
  calIdx = im.getIndex('categoryDate')

  for cid in ids:
    confIds = calIdx.getObjectsInDays(cid, startdate, enddate)
    res.union_update(confIds)

  res = list(res)
  res.sort(sortByStartDate)

  return displayList(res,tz)


def usage():
  return "usage: createCategoryHeader.py?fid=xxx&date=yyyy-mm-dd";

def sortByStartDate(conf1,conf2):
  return cmp(conf1.getStartDate().time(), conf2.getStartDate().time())

def displayList(res,tz):
  text = ""
  curDate = None

  for c in res:
    if curDate!=c.getAdjustedStartDate(tz):
      curDate = c.getAdjustedStartDate(tz)
      text += "%s<br>" % curDate.strftime("%A %B %d, %Y")
    text += displayConf(c,tz)
  return text

def displayConf(conf,tz):
    room = conf.getRoom()
    t = "<b>%s</b>&nbsp;/&nbsp;%s&nbsp;/&nbsp;<a href=\"http://indico.cern.ch/conferenceDisplay.py?confId=%s\">%s</a>/%s" % (conf.getAdjustedStartDate(tz).time().isoformat()[0:5],getCategText(conf.getOwnerList()[0]),conf.getId(),conf.getTitle(), (room.getName() if room else ''))
    return t

def getCategText(categ):
  global ids
  if categ == None:
    return ""
  if categ.getId() in ids:
    return categ.getName()
  else:
    return "%s&nbsp;/&nbsp;%s" % (getCategText(categ.getOwner()),categ.getName())

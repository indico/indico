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

import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.common import xmlGen
from MaKaC.common.Configuration import Config
from MaKaC.common import indexes
from MaKaC.conference import ConferenceHolder
import sets
from pytz import timezone
from MaKaC.common.timezoneUtils import nowutc
import MaKaC.common.info as info
 
class CategoryToRSS:

    def __init__(self, categ, date=None, tz=None):
        self._categ = categ
        self._date = date
        if not tz:
            self._tz = 'UTC'
        else:
            self._tz = tz

    def getBody(self):
        res = sets.Set()
        im = indexes.IndexesHolder()
        catIdx = im.getIndex('category')
        calIdx = im.getIndex('calendar')
        if self._date == None:
            c1 = calIdx.getObjectsEndingAfter(nowutc().astimezone(timezone(self._tz)))
        else:
            date = self._date
            c1 = calIdx.getObjectsInDay(date)
        confIds=sets.Set(catIdx.getItems(self._categ.getId()))
        confIds.intersection_update(c1)
        res.union_update(confIds)
        res = list(res)
        res.sort(sortByStartDate)
        rss = xmlGen.XMLGen()
        rss.openTag('rss version="2.0"')
        rss.openTag("channel")
        rss.writeTag("title","Indico RSS Feed for category %s" % self._categ.getTitle())

        rss.writeTag("link", Config.getInstance().getBaseURL())

        rss.writeTag("description","Forthcoming meetings in category %s" % self._categ.getTitle())
        rss.writeTag("language","en")
        rss.writeTag("pubDate", nowutc().astimezone(timezone(self._tz)).strftime("%a, %d %b %Y %H:%M:%S %Z"))
        rss.writeTag("category","")
        rss.writeTag("generator", "CDS Indico %s" % Config.getInstance().getVersion())
        rss.writeTag("webMaster", info.HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail())
        rss.writeTag("ttl","1440")
        for confId in res:
            ch = ConferenceHolder()
            conf = ch.getById(confId)
            rss = ConferenceToRSS(conf, tz=self._tz).getCore(rss)
        rss.closeTag("channel")
        rss.closeTag("rss")
        return rss.getXml()

class ConferenceToRSS:
    
    def __init__(self, conf, tz=None):
        self._conf = conf
        self._protected = conf.hasAnyProtection()

        if not tz:
            self._tz = 'UTC'
        else:
            self._tz = tz

    def getCore(self, rss):
        date = str(self._conf.getAdjustedStartDate(self._tz).strftime("%a, %d %b %Y %H:%M:%S %Z"))
        title = "%s - %s" % (date, self._conf.getTitle())
        if Config.getInstance().getShortEventURL() != "":
            url = "%s%s" % (Config.getInstance().getShortEventURL(),self._conf.getId())
        else:
            url = urlHandlers.UHConferenceDisplay.getURL( self._conf )
        rss.openTag("item")
        rss.writeTag("title", title )
        rss.writeTag("link",url)

        if not self._protected:
            desc = self._conf.getDescription()
        else:
            desc = ""

        rss.writeTag("description", desc )        
        rss.writeTag("pubDate", self._conf.getAdjustedModificationDate(self._tz).strftime("%a, %d %b %Y %H:%M:%S %Z"))
        rss.writeTag("guid",url)
        rss.closeTag("item")
        return rss

def sortByStartDate(conf1,conf2):
  ch = ConferenceHolder()
  return cmp(ch.getById(conf1).getStartDate(),ch.getById(conf2).getStartDate())

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
import struct, socket


# TOREMOVE
def ACLfiltered(iter, requestIP, aw=None):

    def _inIPList(iplist, ip):

        for rule in iplist:
            if '/' in rule:
                # it's a netmask (CIDR), check if ip belongs to it
                # ipv4-specific, non-endian-safe check!
                ipaddr = struct.unpack('L', socket.inet_aton(ip))[0]
                netaddr, bits = rule.split('/')
                netmask = struct.unpack('L', socket.inet_aton(netaddr))[0] & ((2L << int(bits) - 1) - 1)
                if ipaddr & netmask == netmask:
                    return True
            else:
                if ip in iplist:
                    return True
        return False

    acl = Config.getInstance().getExportACL().iteritems()
    blIds = list(categ for (categ, iplist) in acl if (not _inIPList(iplist, requestIP)))

    for conf in iter:
        owners = list(categ.getId() for categ in conf.getOwnerPath()) + ['0']
        for blId in blIds:
            if blId in owners:
                if aw and aw.getUser() and conf.canAccess(aw):
                    yield conf
                else:
                    break
        else:
            yield conf


class CategoryToRSS:

    def __init__(self, categ, req, date=None, tz=None):
        self._categ = categ
        self._date = date
        if not tz:
            self._tz = 'UTC'
        else:
            self._tz = tz
        self._req = req

    def getBody(self):
        im = indexes.IndexesHolder()
        calIdx = im.getIndex('categoryDate')

        if self._date == None:
            confs = calIdx.getObjectsEndingAfter(self._categ.getId(), nowutc().astimezone(timezone(self._tz)))
        else:
            confs = calIdx.getObjectsInDay(self._categ.getId(), self._date)

        sconfs = set()

        sconfs = set(ACLfiltered(confs, self._req.getHostIP(), self._req.getAW()))
        res = list(sconfs)
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
        for conf in res:
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
  return cmp(conf1.getStartDate(), conf2.getStartDate())

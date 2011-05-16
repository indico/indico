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
from MaKaC.common.xmlGen import XMLGen
from MaKaC.rb_location import CrossLocationQueries
from MaKaC.rb_reservation import Collision
import os, sys, csv, tempfile, stat
from datetime import datetime, timedelta
from indico.web.wsgi import webinterface_handler_config as apache
from MaKaC.common import DBMgr
from MaKaC.rb_factory import Factory
from MaKaC.common.Configuration import Config
from MaKaC.common.datetimeParser import parse_date
from MaKaC.domain import DomainHolder
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.errors import HostnameResolveError
from MaKaC.webinterface.urlHandlers import UHRoomBookingBookingDetails
from MaKaC.common.utils import parseDate

"""
TODO: This must be refactor to be done with RH???
"""

def index(req, **params):

    DBMgr.getInstance().startRequest()
    Factory.getDALManager().connect()

    ################### checking protection ###################

    def getHostIP(req):
        import socket

        host = str(req.get_remote_host(apache.REMOTE_NOLOOKUP))

        try:
            hostIP = socket.gethostbyname(host)
            minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
            if minfo.useProxy():
                # if we're behind a proxy, use X-Forwarded-For
                xff = req.headers_in.get("X-Forwarded-For",hostIP).split(", ")[-1]
                return socket.gethostbyname(xff)
            else:
                return hostIP
        except socket.gaierror, e:
            # in case host resolution fails
            raise HostnameResolveError("Error resolving host '%s' : %s" % (host, e))


    # check if it is a machine that belongs to the CERN domain
    cernDomain = DomainHolder().getById(0) # id 0 means CERN
    if not cernDomain.belongsTo(getHostIP(req)):
        return "Only CERN users can access to this export resource"

    ################### checking params ###################
    if not (params.has_key("sd") and params.has_key("ed") and params.has_key("r")):
        return """Missing parameters. The request should be like this: http://indico.cern.ch/exportReservations.py?sd=2010-09-24&ed=2010-09-25&r=1,18,114,42"""

    try:
        sd = parseDate(params.get("sd"), "%Y-%m-%d")
        ed = parseDate(params.get("ed"), "%Y-%m-%d")
    except ValueError, e:
        return """The format for the dates (sd and ed) must be like this: YYYY-MM-DD"""
    if sd > ed:
        return """'sd' must be <= than 'ed'"""
    if ed - sd > timedelta(35):
        return """One can only export 3 days at most"""


    roomIDs = params.get("r").strip().split(",")
    if roomIDs == "":
        return """At least one roomID must be specified (http://....?r=1,42,14,...)"""
    try:
        roomIDs = map(lambda x: int(x), roomIDs)
    except ValueError:
        return """Room IDs must be integers separated by commas (http://....?r=1,42,14,...)"""
    if len(roomIDs) > 10:
        return "One can only export 10 rooms at most"

    #################### process ###################
    rooms = []
    for roomID in roomIDs:
        roomEx = Factory.newRoom()
        roomEx.id = roomID
        rooms.append(roomEx)

    resvEx = Factory.newReservation()
    resvEx.isCancelled = False
    resvEx.isRejected = False
    resvEx.startDT = datetime(sd.year, sd.month, sd.day, 0, 0)
    resvEx.endDT = datetime(ed.year, ed.month, ed.day, 23, 59)
    resvs = CrossLocationQueries.getReservations(location="CERN", resvExample=resvEx, rooms=rooms)
    collisions = []
    for resv in resvs:
        for p in resv.splitToPeriods(endDT=resvEx.endDT, startDT=resvEx.startDT):
            collisions.append(Collision( ( p.startDT, p.endDT ), resv ))

    of = params.get("of", "csv")
    if of == "xml":
        result = createXML(collisions, req)
    else:
        result = createCSV(collisions, req)

    Factory.getDALManager().disconnect()
    DBMgr.getInstance().endRequest()

    return result


def createXML(resvs, req):

    req.content_type="text/xml"

    xml = XMLGen()

    xml.openTag("bookings")

    for collision in resvs:
        resv = collision.withReservation
        xml.openTag("booking")
        xml.writeTag("room", "%s %s-%s"%(str(resv.room.building), resv.room.floor, str(resv.room.roomNr)))
        xml.writeTag("startTime", collision.startDT.strftime("%Y-%m-%d %H:%M:%S"))
        xml.writeTag("endTime", collision.endDT.strftime("%Y-%m-%d %H:%M:%S"))
        xml.writeTag("reason", resv.reason or "")
        xml.closeTag("booking")

    xml.closeTag("bookings")

    return xml.getXml()



def createCSV(resvs, req):

    results=[['URL',
             'id',
             'start date',
             'end date',
             'name',
             'site',
             'building',
             'floor',
             'roomNr',
             'IP',
             'H323 IP',
             'uses VC equipment'
             ]]

    for collision in resvs:
        resv = collision.withReservation
        if resv.usesAVC:
            usesAVC = 1
        else:
            usesAVC = 0
        results.append([str(UHRoomBookingBookingDetails.getURL(resv)),
                         str(resv.id),
                         collision.startDT.strftime("%Y-%m-%d %H:%M:%S"),
                         collision.endDT.strftime("%Y-%m-%d %H:%M:%S"),
                         resv.room.name or "",
                         resv.room.site,
                         str(resv.room.building),
                         resv.room.floor,
                         str(resv.room.roomNr),
                         resv.room.customAtts.get('IP') or "",
                         resv.room.customAtts.get('H323 IP') or "",
                         usesAVC
                         ])



    #################### create temp file ###################
    cfg = Config.getInstance()
    tempPath = cfg.getUploadedFilesTempDir()
    tempFileName = tempfile.mkstemp( prefix="Bookings", suffix=".csv", dir = tempPath )[1]

    #################### write the results in the temp file ###################
    fd=open(tempFileName, 'w')
    writer = csv.writer(fd, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    for i in results:
        writer.writerow(i)
    fd.close()

    #################### return the CSV file ###################
    req.headers_out["Content-Length"] = "%s"%int(os.stat(tempFileName)[stat.ST_SIZE])
    mimetype = cfg.getFileTypeMimeType( cfg.getFileType("CSV") )
    req.content_type = """%s"""%(mimetype)
    req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%os.path.basename(tempFileName)

    fr = open(tempFileName, "rb")
    data = fr.read()
    fr.close()
    return data

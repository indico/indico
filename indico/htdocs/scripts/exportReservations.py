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
import os, sys, csv, tempfile, stat
from datetime import datetime, timedelta
from mod_python import apache
from MaKaC.common import DBMgr
from MaKaC.rb_factory import Factory
from MaKaC.common.Configuration import Config
from MaKaC.common.datetimeParser import parse_date
from MaKaC.domain import DomainHolder
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.errors import HostnameResolveError
from MaKaC.webinterface.urlHandlers import UHRoomBookingBookingDetails

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
        return """Missing parameters. The request should be like this: http://indico.cern.ch/exportRooms.py?sd=24-09-2010&ed=25-09-2010&r=1,18,114,42"""

    try:
        sd = parse_date(params.get("sd"))
        ed = parse_date(params.get("ed"))
    except ValueError, e:
        return """The format for the dates (sd and ed) must be like this: DD-MM-YYYY"""
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
    if len(roomIDs) > 20:
        return "One can only export 10 rooms at most"

    #################### process ###################

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
             'H323 IP\n'
             ]]

    rooms = []
    for roomID in roomIDs:
        roomEx = Factory.newRoom()
        roomEx.id = roomID
        rooms.append(roomEx)

    resvEx = Factory.newReservation()
    resvEx.startDT = datetime(sd.year, sd.month, sd.day, 0, 0)
    resvEx.endDT = datetime(ed.year, ed.month, ed.day, 23, 59)
    resvs = resvEx.getCollisions(rooms = rooms )

    for collision in resvs:
        resv = collision.withReservation
        results.append([str(UHRoomBookingBookingDetails.getURL(resv)),
                         str(resv.id),
                         collision.startDT.strftime("%d-%m-%Y %H:%M"),
                         collision.endDT.strftime("%d-%m-%Y %H:%M"),
                         resv.room.name or "",
                         resv.room.site,
                         str(resv.room.building),
                         resv.room.floor,
                         str(resv.room.roomNr),
                         resv.room.customAtts.get('IP') or "",
                         resv.room.customAtts.get('H323 IP') or "" + '\n'
                         ])

    Factory.getDALManager().disconnect()
    DBMgr.getInstance().endRequest()

    #################### create temp file ###################
    cfg = Config.getInstance()
    tempPath = cfg.getUploadedFilesTempDir()
    tempFileName = tempfile.mkstemp( prefix="Bookings", suffix=".csv", dir = tempPath )[1]

    #################### write the results in the temp file ###################
    fd=open(tempFileName, 'w')
    writer = csv.writer(fd, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
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


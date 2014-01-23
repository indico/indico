# -*- coding: utf-8 -*-
##
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

"""
It sends emails to all the primary authors and speakers
NOTE: Please, comment the "return" below this line in order
to run the code. It was put just like a security reason.
"""

import sys
sys.path.append('/soft/python/lib/python2.3/site-packages')

import smtplib
from indico.core.config import Config
from indico.core.db import DBMgr
from MaKaC import conference

def getToList():
    toList = []
    DBMgr.getInstance().startRequest()
    ch = conference.ConferenceHolder()
    c = ch.getById("0")
    toList = []
    i = 0
    for contrib in c.getContributionList():
        if contrib.getPaper() == None or contrib.getPaper().getResourceList() == []:
            if not isinstance(contrib.getCurrentStatus(), conference.ContribStatusWithdrawn):
                i += 1
                for pa in contrib.getPrimaryAuthorList():
                    if pa.getEmail().strip() != "" and (not pa.getEmail() in toList):
                        toList.append(pa.getEmail())
                for spk in contrib.getSpeakerList():
                    if spk.getEmail().strip() != "" and (not spk.getEmail() in toList):
                        toList.append(spk.getEmail())
    DBMgr.getInstance().endRequest()
    print "Number of contribs without papers:%s"%i
    return toList

toList = getToList()
print "len of toList:%s"%len(toList)
toList.append("Nathalie.Knoors@cern.ch")
fromAddr="pc-secretary@chep04.org"
subject="CHEP04 - Submission of papers"
body="""
     Dear Presenters,

     This is a reminder that we are approaching the deadline for submitting
     your materials - October 15th - 1 day left to submit your paper for
     publication in the proceedings.

     For your information, if there are several files sources, you may send
     your materials in one single zipped file.

     John Harvey

     Chair Programme Committee
     """

log = open('./email.log','w')
logErrors = open('./emailErrors.log','w')
server=smtplib.SMTP(Config.getInstance().getSmtpServer())
if Config.getInstance().getSmtpUseTLS():
    server.ehlo()
    (code, errormsg) = server.starttls()
    if code != 220:
        from MaKaC.errors import MaKaCError
        raise MaKaCError("Can't start secure connection to SMTP server: %d, %s"%(code,errormsg))
if Config.getInstance().getSmtpLogin():
    login = Config.getInstance().getSmtpLogin()
    password = Config.getInstance().getSmtpPassword()
    (code, errormsg) = server.login(login, password)
    if code != 235:
        from MaKaC.errors import MaKaCError
        raise MaKaCError("Can't login on SMTP server: %d, %s"%(code, errormsg))
for to in toList:
    cc=""
    msg="From: %s\r\nTo: %s\r\n%sSubject: %s\r\n\r\n%s"%(fromAddr, to,cc,subject,body)
    try:
        server.sendmail(fromAddr,[to],msg)
        log.write("%s\n"%to)
    except:
        logErrors.write("%s\n"%to)
        pass
server.quit()
log.write("DONE")
logErrors.write("DONE")
log.close()
logErrors.close()
print "done"

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
raise Exception("delete this line to run the code")

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
    for contrib in c.getContributionList():
        if not isinstance(contrib.getCurrentStatus(), conference.ContribStatusWithdrawn):
            for pa in contrib.getPrimaryAuthorList():
                if pa.getEmail().strip() != "" and (not pa.getEmail() in toList):
                        toList.append(pa.getEmail())
            for spk in contrib.getSpeakerList():
                if spk.getEmail().strip() != "" and (not spk.getEmail() in toList):
                        toList.append(spk.getEmail())
    DBMgr.getInstance().endRequest()
    return toList

toList = getToList()
toList.append("Nathalie.Knoors@cern.ch")
fromAddr="Nathalie Knoors <Nathalie.Knoors@cern.ch>"
subject="CHEP04 - Submission of papers"
body="""
Dear CHEP04 presenters,

On behalf of the Programme Committee (PC) I would like to thank all of you for the excellent talks and posters presented last week at CHEP04. We thank especially those of you (the majority) who have already submitted your paper for publication in the proceedings. The PC will now start to process these papers and you may be contacted in the case any changes are required.

We have received several requests for a short extension of the deadline. In order to accommodate these requests the deadline for submission of papers is hereby extended until October 15th. We would be very grateful if you will respect this deadline so that we can get the proceedings published in a timely manner.

many thanks in advance for your cooperation,

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
        raise MaKaCError("Can't start secure connection to SMTP server: %d, %s"%(code, errormsg))
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

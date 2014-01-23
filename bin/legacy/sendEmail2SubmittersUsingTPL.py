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

#import sys
#sys.path.append('/soft/python/lib/python2.3/site-packages')

import smtplib
from indico.core.config import Config
from indico.core.db import DBMgr
from MaKaC import conference
from MaKaC.webinterface import urlHandlers

errorlogfile = "/tmp/sendemail2sub.error.log"
logfile = "/tmp/sendemail2sub.log"

CONF_ID="35523"
CONTRIBS_IDS = [1,9,10,11,12,13,15,17,18,19,20,23,25,27,28,30,31,33,34,35,36,38,39,41,43,44,48,50,53,54,55,56,57,58,60,61,64,65,67,68,69,70,71,73,74,75,76,77,78,79,80,82,83,84,85,86,87,89,91,92,95,96,97,98,99,101,102,105,106,107,108,110,112,113,114,116,117,118,119,120,121,122,123,124,125,128,130,132,133,134,136,139,141,142,143,144,145,146,147,148,151,153,154,155,156,158,159,160,162,163,164,165,166,171,172,173,174,176,179,180,182,187,188,189,190,192,196,197,200,201,202,203,204,205,206,207,209,210,213,214,215,216,217,218,220,223,224,225,226,227,228,229,230,231,232,233,234,235,237,238,239,240,241,242,243,245,246,249,251,252,254,255,256,258,259,261,262,263,264,265,266,268,269,270,272,274,275,276,277,278,279,280,281,282,283,284,285,287,288,290,291,292,293,294,295,296,301,305,307,309,311,312,315,316,318,319,322,323,325,326,328,329,330,331,332,333,337,341,342,343,344,345,347,348,349,352,353,354,355,356,357,358,360,361,362,363,364,365,369,370,372,373,374,375,377,378,380,381,382,383,384,385,386,387,388,389,391,395,396,397,398,399,400,402,403,404,405,406,407,408,409,411,412,413,414,416,418,419,420,423,426,427,428,429,430,431,432,434,435,437,439,440,441,442,443,444,445,447,448,449,450,452,453,456,457,460,462,463,466,467,468,469,472,473,475,477,479,480,482,483,484,485,486,487,488,489,490,491,492,493,494,495,497,498,502,505,506,508,533,2,7,14,16,24,32,45,51,52,59,63,66,81,88,90,93,100,109,111,115,126,127,129,135,140,149,168,169,170,175,177,181,183,184,186,191,194,195,198,199,212,221,222,236,244,247,248,260,267,271,273,286,289,298,299,304,308,321,324,327,335,336,338,339,340,346,350,351,366,368,371,376,379,401,410,415,417,421,422,425,436,446,451,459,464,470,474,476,478,500]

FROM = "chep2009@particle.cz"
subjectTPL = "CHEP2009 - Abstract - final status"

bodyTPL = """

Dear %(submitter_first_name)s %(submitter_family_name)s

Your abstract "%(abstract_title)s" was finally accepted as %(contribution_type)s presentation and is assigned to the %(abstract_track)s.

For the further information (as the reviewer or Program Committee comments) see:
%(abstract_URL)s

We plan that all contributions, oral and posters, will be published in a
reviewed electronic journal, i.e. they will be standard references.


Detailed information about conference program will be available soon.

Best regards
Ludek Matyska
on behalf of Program Committee



Registration information:
If you have not done it yet, please complete your registration on the following website: https://secure.guarant.cz/chep2009/UserPages/InteractiveAppForms.aspx

Log in with your password which you have received while filling in the personal data when submitting your abstract and complete the registration process by choosing the registration fee.

"""

server=smtplib.SMTP(Config.getInstance().getSmtpServer())

def checkSMTPServer():
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
    return True

def errorlog(msg):
    print msg
    f=open(errorlogfile,'a')
    f.write("%s\n"%msg)
    f.close()

def log(msg):
    print msg
    f=open(logfile,'a')
    f.write("%s\n"%msg)
    f.close()

def getBody(contrib):
    abs=contrib.getAbstract()
    subm=abs.getSubmitter()
    d={"submitter_first_name": subm.getFirstName(),
       "submitter_family_name": subm.getSurName(),
       "abstract_title": abs.getTitle().decode('utf-8').encode('utf-8'),
       "contribution_type": contrib.getType().getName(),
       "abstract_track": contrib.getTrack().getTitle(),
       "abstract_URL": urlHandlers.UHAbstractDisplay.getURL(abs)}
    return bodyTPL%d

def sendEmail(contrib):
    abstract = contrib.getAbstract()

    to = abstract.getSubmitter().getEmail()
    fromAddr = FROM
    subject = subjectTPL
    body=getBody(contrib)
    cc=""

    msg="From: %s\r\nTo: %s\r\n%sSubject: %s\r\n\r\n%s"%(fromAddr, to,cc,subject,body)
    try:
        server.sendmail(fromAddr,[to],msg)
        log(to)
    except:
        errorlog(to)
    log("%s\n\n\n\n\n\n\n\n"%msg)




if __name__ == "__main__":
    if checkSMTPServer():
        DBMgr.getInstance().startRequest()
        ch = conference.ConferenceHolder()
        c = ch.getById(CONF_ID)
        DBMgr.getInstance().endRequest()
        counter = 0
        for contribId in CONTRIBS_IDS:
            DBMgr.getInstance().startRequest()
            contrib = c.getContributionById(contribId)
            if isinstance(contrib,conference.AcceptedContribution):
               sendEmail(contrib)
               counter += 1
            else:
               errorlog("contrib %s is not AcceptedContribution")

            DBMgr.getInstance().endRequest()


        server.quit()
        log("[DONE] %s emails sent"%counter)
        errorlog("DONE")

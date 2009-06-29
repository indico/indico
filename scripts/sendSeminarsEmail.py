# -*- coding: utf-8 -*-
##
## $Id: sendSeminarsEmail.py,v 1.2 2008/04/24 17:00:22 jose Exp $
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

import urllib2
from datetime import datetime,timedelta
from MaKaC.webinterface.mail import GenericMailer,GenericNotification

date = (datetime.today()+timedelta(days=(7-int(datetime.today().strftime('%w'))))).strftime("%Y-%m-%d")
text = ""

url = "http://indico.cern.ch/tools/export.py?fid=1l7&date=%s&days=14&of=html" % date
req = urllib2.Request(url)
f = urllib2.urlopen(req)
text = f.read()
f.close()

data = {}
data['fromAddr'] = ""
data['toList'] = ["christiane.lefevre@cern.ch","thomas.baron@cern.ch"]
data['subject'] = "Seminars for the coming two weeks"
data['body'] = text
data['content-type'] = "text/html"
mail = GenericNotification(data)

GenericMailer().send(mail)


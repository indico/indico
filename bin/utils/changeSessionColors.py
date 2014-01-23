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

from indico.core.db import DBMgr
from MaKaC.conference import ConferenceHolder

DBMgr.getInstance().startRequest()

confId = "18714"
translations = { "#FFCC00": "#FFCC66",
                 "#6699CC": "#66CCFF",
                 "#33CC00": "#99FF66",
                 "#9900FF": "#CC99FF",
                 "#FFFF00": "#FFFF99" }

ch = ConferenceHolder()

conf = ch.getById(confId)

for ses in conf.getSessionList():
  oc = ses.getColor()
  if translations.get(oc,"") != "":
    nc = translations[oc]
    ses.setColor(nc)

DBMgr.getInstance().endRequest()

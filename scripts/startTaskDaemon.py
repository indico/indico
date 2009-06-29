# -*- coding: utf-8 -*-
##
## $Id: startTaskDaemon.py,v 1.10 2008/04/24 17:00:20 jose Exp $
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

import sys
# Append the path to the MaKaC folder:
#sys.path.append('C:/development/indico/code/code')
#from MaKaC.conference import CategoryManager
#from MaKaC.common import DBMgr
#from datetime import timedelta, datetime
try:
    from MaKaC.common.timerExec import toExec, timer#, HelperTaskList, StatisticsUpdater, task
except ImportError, e:
    print "ImportError:%s"%e
    sys.exit(0)
"""
Run the function listed in the toExec instance each 'duration' seconds
"""
duration = 3600 # seconds
te = toExec()
t = timer(duration, te.execute)

#print "...:::Daemaon started:::...\n\n"
#DBMgr.getInstance().startRequest()
#tl = HelperTaskList.getTaskListInstance()
#catRoot = CategoryManager().getRoot()
#try:
#    if catRoot.statsUpdater != None:
#        tl.removeTask(catRoot.statsUpdater)
#        catRoot.statsUpdater = None
#except:
#    catRoot.statsUpdater = None
#su = StatisticsUpdater(catRoot)
#ta = task()
#d = datetime.now() + timedelta(days=1)
#ta.setStartDate(datetime(d.year, d.month, d.day, 0, 0))
#ta.setInterval(timedelta(days=1))
#ta.addObj(su)
#tl.addTask(ta)
#catRoot.statsUpdater = ta
#DBMgr.getInstance().endRequest()

t.start()


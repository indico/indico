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

from MaKaC.common import DBMgr
from MaKaC.common.Counter import Counter
from MaKaC.conference import ConferenceHolder
from MaKaC.common.timerExec import HelperTaskList


def runTaskMigration():
    DBMgr.getInstance().startRequest()

    for t in HelperTaskList().getTaskListInstance().getTasks():
        print t

    DBMgr.getInstance().endRequest()


def runConferenceMigration():
    DBMgr.getInstance().startRequest()
    ch = ConferenceHolder()

    for conf in ch.getList():
        if hasattr(conf, '__alarmCounter'):
            raise Exception("Conference Object %s (%s) seems to have been already "
                            "converted" % (conf, conf.id))

        existingKeys = conf.alarmList.keys()
        existingKeys.sort()
        conf._Conference__alarmCounter = Counter(int(existingKeys[-1]) + 1)

        # TODO: For each conference, take the existing tasks and convert them to
        # the new object classes.
        # It is important to save the state of the alarm (sent or not)

    DBMgr.getInstance().endRequest()


def runPluginMigration():

    # TODO: for each Plugin/PluginType, add __notUsableReason attribute (default None)

def main():
    runTaskMigration()

if __name__ == "__main__":
    main()


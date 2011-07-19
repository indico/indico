# -*- coding: utf-8 -*-
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

"""
Migration script: v0.97 -> v0.98
"""

import sys, traceback, argparse
from BTrees.OOBTree import OOTreeSet
from dateutil import rrule

from MaKaC.common.indexes import IndexesHolder, CategoryDayIndex
from MaKaC.common import DBMgr
from MaKaC.common.Counter import Counter
from MaKaC.conference import ConferenceHolder, CategoryManager, Conference
from MaKaC.common.timerExec import HelperTaskList
from MaKaC.plugins.base import PluginType, PluginsHolder
from MaKaC.registration import RegistrantSession, RegistrationSession
from MaKaC.plugins.RoomBooking.default.dalManager import DALManager

from indico.core.index import Catalog
from indico.ext import livesync
from indico.util import console
from indico.modules.scheduler.tasks import AlarmTask, FoundationSyncTask, \
     CategoryStatisticsUpdaterTask

from indico.modules.scheduler import Client


def runTaskMigration(dbi, withRBDB):
    """
    Migrating database tasks from the old format to the new one
    """

    c = Client()

    for t in HelperTaskList().getTaskListInstance().getTasks():
        for obj in t.getObjList():
            print console.colored("   * %s" % obj.__class__.__name__, 'blue')
            if obj.__class__.__name__ == 'FoundationSync':
                c.enqueue(
                    FoundationSyncTask(rrule.DAILY, byhour=0, byminute=0))
            elif obj.__class__.__name__ == 'StatisticsUpdater':
                c.enqueue(CategoryStatisticsUpdaterTask(
                    CategoryManager().getById('0'),
                    rrule.DAILY,
                    byhour=0, byminute=0))
            elif obj.__class__.__name__ == 'sendMail':
                # they have to be somewhere in the conference
                alarm = t.conf.alarmList[t.id]
                c.enqueue(alarm)
            else:
                raise Exception("Unknown task type!")

    if withRBDB:
        DALManager.commit()
    dbi.commit()


def _fixAC(obj):
    ac = obj.getAccessController()
    ac.setOwner(obj)


def _fixAccessController(obj, fixSelf=True):
    # i.e. subcontributions do not have their own AccessController
    if fixSelf:
        _fixAC(obj)

    for mat in obj.getAllMaterialList():
        for res in mat.getResourceList():
            _fixAC(res)
        _fixAC(mat)


def _convertAlarms(obj):
    """
    Take the alarms in an event and convert them to the new format
    """
    alarms = {}
    obj._legacyAlarmList = obj.getAlarmList()

    for alarm in obj.getAlarmList():
        sdate = alarm.getStartDate()
        newTask = AlarmTask(obj, alarm.id, sdate)
        newTask.setSubject(alarm.getSubject())
        newTask.setText(alarm.getText())

        # define directly, otherwise _setText will be triggered!
        newTask.note = alarm.getNote()
        newTask.confSummary = alarm.getConfSumary()

        newTask.setToAllParticipants(alarm.getToAllParticipants())
        alarms[alarm.id] = newTask

        newTask.setFromAddr(alarm.getFromAddr())
        for addr in alarm.getToAddrList():
            newTask.addToAddr(addr)

    obj.alarmList = alarms


def runCategoryACMigration(dbi, withRBDB):
    """
    Fixing AccessController for categories
    """
    for categ in CategoryManager()._getIdx().itervalues():
        _fixAccessController(categ)
        dbi.commit()


def runConferenceMigration(dbi, withRBDB):
    """
    Adding missing attributes to conference objects and children
    """

    ch = ConferenceHolder()
    i = 0

    for (level, obj) in console.conferenceHolderIterator(ch, deepness='subcontrib'):
        # only for conferences
        if level == 'event':

            # handle sessions, that our iterator ignores
            for session in obj.getSessionList():
                _fixAccessController(session)

            if hasattr(obj, '_Conference__alarmCounter'):
                raise Exception("Conference Object %s (%s) seems to have been "
                                "already converted" % (obj, obj.id))

            existingKeys = obj.alarmList.keys()
            existingKeys.sort()
            nstart = int(existingKeys[-1]) + 1 if existingKeys else 0
            obj._Conference__alarmCounter = Counter(nstart)

            # For each conference, take the existing tasks and
            # convert them to the new object classes.
            _convertAlarms(obj)

        _fixAccessController(obj,
                             fixSelf=(level != 'subcontrib'))

        # Convert RegistrationSessions to RegistrantSessions
        if isinstance(obj, Conference):
            for reg in obj.getRegistrants().itervalues():
                if reg._sessions and \
                       isinstance(reg._sessions[0], RegistrationSession):
                    reg._sessions = [RegistrantSession(ses, reg) \
                                     for ses in reg._sessions]

        if i % 1000 == 999:
            dbi.commit()
            if withRBDB:
                DALManager.commit()

        i += 1

    dbi.commit()
    if withRBDB:
        DALManager.commit()


def runPluginMigration(dbi, withRBDB):
    """
    Adding new plugins and adapting existing ones to new name policies
    """
    root = dbi.getDBConnection().root()
    if 'plugins' in root:
        ptl = []
        ps = root['plugins']
        for k, v in ps.iteritems():
            if isinstance(v, PluginType):
                ptl.append(v)
        for pt in ptl:
            pt.setUsable(True)
            for p in pt.getPluginList(includeNonPresent=True,
                                      includeTestPlugins=True,
                                      includeNonActive=True):
                # new ids have no spaces
                p.setId(p.getName().replace(" ", ""))
                p.setUsable(True)
    dbi.commit()
    if withRBDB:
        DALManager.commit()

    # load new plugins, so that we can update them after
    PluginsHolder().reloadAllPlugins()
    dbi.commit()
    if withRBDB:
        DALManager.commit()

    # update db for specific plugins
    livesync.db.updateDBStructures(root)
    dbi.commit()
    if withRBDB:
        DALManager.commit()


def runCategoryDateIndexMigration(dbi, withRBDB):
    """
    Replacing category date indexes.
    """
    if "backupCategoryDate" not in IndexesHolder()._getIdx():
        categoryDate = IndexesHolder().getIndex("categoryDate")
        IndexesHolder()._getIdx()["backupCategoryDate"] = categoryDate
        newIdx = CategoryDayIndex()
        newIdx.buildIndex()
        IndexesHolder()._getIdx()["categoryDate"] = newIdx
    else:
        print """runCategoryDateIndexMigration: new categoryDate index has """ \
        """NOT been generated because the index backup already exists.

If you still want to regenerate it, please, do it manually using """ \
        """bin/migration/CategoryDate.py"""


def runCatalogMigration(dbi, withRBDB):
    """
    Initializing the new index catalog
    """
    Catalog.updateDB(dbi=dbi)


def runCategoryConfDictToTreeSet(dbi, withRBDB):
    """
    Replacing the conference dictionary in the Category objects by a OOTreeSet.
    """
    for categ in CategoryManager()._getIdx().itervalues():
        categ.conferencesBackup = categ.conferences.values()
        categ.conferences = OOTreeSet(categ.conferences.itervalues())
        if len(categ.conferences) != len(categ.conferencesBackup):
            print "Problem migrating conf dict to tree set: %s" % categ.getId()


def runMigration(withRBDB=False):

    tasks = [runPluginMigration,
             runCategoryACMigration,
             runConferenceMigration,
             runTaskMigration,
             runCategoryConfDictToTreeSet,
             runCategoryDateIndexMigration,
             runCatalogMigration]

    print "\nExecuting migration...\n"

    dbi = DBMgr.getInstance()

    for task in tasks:
        print console.colored("->", 'green', attrs=['bold']), \
              task.__doc__.replace('\n', '').strip()
        dbi.startRequest()
        if withRBDB:
            DALManager.connect()

        task(dbi, withRBDB)

        if withRBDB:
            DALManager.commit()
        dbi.endRequest()

        print console.colored("   DONE\n", 'green', attrs=['bold'])

    print console.colored("Database Migration successful!\n",
                          'green', attrs=['bold'])


def main():
    """
    Main program cycle
    """

    print console.colored("""\nThis script will migrate the Indico DB from v0.97.x to v0.98. We recommend that
this operation be executed while the web server is down, in order to avoid
concurrency problems and DB conflicts.\n\n""", 'yellow')

    parser = argparse.ArgumentParser(description='Execute migration')
    parser.add_argument('--with-rb', dest='useRBDB', action='store_true',
                        help='Use the Room Booking DB')

    args = parser.parse_args()

    if console.yesno("Are you sure you want to execute the "
                     "migration now?"):
        try:
            return runMigration(withRBDB=args.useRBDB)
        except:
            print console.colored("\nMigration failed! DB may be in "
                                  " an inconsistent state:", 'red', attrs=['bold'])
            print console.colored(traceback.format_exc(), 'red')
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())

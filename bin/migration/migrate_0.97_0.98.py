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
from MaKaC.user import AvatarHolder
from MaKaC.rb_location import CrossLocationQueries

"""
Migration script: v0.97 -> v0.98

NOTE: Methods should be specified in order of execution, since @since adds them to
the task list in the order it is called.
"""


import sys, traceback, argparse
from BTrees.OOBTree import OOTreeSet, OOBTree
from BTrees.IOBTree import IOBTree
from dateutil import rrule
from pkg_resources import parse_version

from MaKaC import __version__
from MaKaC.common.indexes import IndexesHolder, CategoryDayIndex, CalendarDayIndex
from MaKaC.common import DBMgr
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.common.Counter import Counter
from MaKaC.conference import ConferenceHolder, CategoryManager, Conference
from MaKaC.common.timerExec import HelperTaskList
from MaKaC.plugins.base import PluginType, PluginsHolder
from MaKaC.registration import RegistrantSession, RegistrationSession
from MaKaC.plugins.RoomBooking.default.dalManager import DALManager
from MaKaC.webinterface import displayMgr

from indico.core.index import Catalog
from indico.ext import livesync
from indico.util import console, i18n
from indico.modules.scheduler.tasks import AlarmTask, FoundationSyncTask, \
     CategoryStatisticsUpdaterTask, RoomReservationTask

from indico.modules.scheduler import Client


MIGRATION_TASKS = []


i18n.setLocale('en_GB')


def since(version):
    def _since(f):
        MIGRATION_TASKS.append((version, f))
        return f
    return _since


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
        if alarm.timeBefore:
            newTask = AlarmTask(obj, alarm.id, relative=alarm.timeBefore)
        elif alarm.getStartDate():
            newTask = AlarmTask(obj, alarm.id, alarm.getStartDate())
        else:
            continue
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


def _fixDefaultStyle(conf, cdmr):
    confDM = cdmr.getDisplayMgr(conf, True)
    if confDM.getDefaultStyle() == 'administrative3':
        confDM.setDefaultStyle('administrative')
    if confDM.getDefaultStyle() == 'it':
        confDM.setDefaultStyle('standard')


@since('0.98b2')
def runPluginMigration(dbi, withRBDB, prevVersion):
    """
    Adding new plugins and adapting existing ones to new name policies
    """

    PLUGIN_REMAP = {
        'PayPal': 'payPal',
        'WorldPay': 'worldPay',
        'YellowPay': 'yellowPay',
        "Dummyimporter": "dummy",
        "CDSInvenio": "invenio",
        "CERNSearchPOST": "cern_search",
        "InvenioBatchUploader": "invenio"
    }

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
                if hasattr(p, '_Plugin__id'):
                    pid = p.getId()
                else:
                    pid = p.getName()

                if pid in PLUGIN_REMAP:
                    pid = PLUGIN_REMAP[pid]

                p.setId(pid)
                p.setUsable(True)

    dbi.commit()
    if withRBDB:
        DALManager.commit()

    # load new plugins, so that we can update them after
    PluginsHolder().reloadAllPlugins()
    dbi.commit()
    if withRBDB:
        DALManager.commit()

    if prevVersion < parse_version("0.98b1"):
        # update db for specific plugins
        livesync.db.updateDBStructures(root)
        dbi.commit()
        if withRBDB:
            DALManager.commit()


@since('0.98b')
def runCategoryACMigration(dbi, withRBDB, prevVersion):
    """
    Fixing AccessController for categories
    """
    for categ in CategoryManager()._getIdx().itervalues():
        _fixAccessController(categ)
        dbi.commit()


@since('0.98b2')
def runConferenceMigration(dbi, withRBDB, prevVersion):
    """
    Adding missing attributes to conference objects and children
    """

    cdmr = displayMgr.ConfDisplayMgrRegistery()
    ch = ConferenceHolder()
    i = 0

    from97 = prevVersion < parse_version("0.98b1")

    # migrating from <=0.97.1 requires smaller granularity
    for (level, obj) in console.conferenceHolderIterator(ch, deepness='subcontrib' if from97 else 'event'):
        # only for conferences
        if level == 'event':

            if from97:
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

            # convert registration form's "Personal Data" section to new format
            obj.getRegistrationForm()._convertPersonalData()

            # For each conference, fix the default style
            _fixDefaultStyle(obj, cdmr)

        if from97:
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
            if withRBDB and from97:
                DALManager.commit()

        i += 1

    dbi.commit()
    if withRBDB and from97:
        DALManager.commit()


@since('0.98b')
def runTaskMigration(dbi, withRBDB, prevVersion):
    """
    Migrating database tasks from the old format to the new one
    """

    c = Client()

    for t in HelperTaskList().getTaskListInstance().getTasks():
        for obj in t.listObj.values():
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


@since('0.98b')
def runCategoryConfDictToTreeSet(dbi, withRBDB, prevVersion):
    """
    Replacing the conference dictionary in the Category objects by a OOTreeSet.
    """
    for categ in CategoryManager()._getIdx().itervalues():
        categ.conferencesBackup = categ.conferences.values()
        categ.conferences = OOTreeSet(categ.conferences.itervalues())
        if len(categ.conferences) != len(categ.conferencesBackup):
            print "Problem migrating conf dict to tree set: %s" % categ.getId()


@since('0.98b')
def runCategoryDateIndexMigration(dbi, withRBDB, prevVersion):
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


@since('0.98b')
def runCatalogMigration(dbi, withRBDB, prevVersion):
    """
    Initializing the new index catalog
    """
    Catalog.updateDB(dbi=dbi)


@since('0.98b2')
def runRoomBlockingInit(dbi, withRBDB, prevVersion):
    """
    Initializing room blocking indexes.
    """
    if not withRBDB:
        return

    root = DALManager().getRoot()
    if not root.has_key( 'RoomBlocking' ):
        root['RoomBlocking'] = OOBTree()
        root['RoomBlocking']['Blockings'] = IOBTree()
        root['RoomBlocking']['Indexes'] = OOBTree()
        root['RoomBlocking']['Indexes']['OwnerBlockings'] = OOBTree()
        root['RoomBlocking']['Indexes']['DayBlockings'] = CalendarDayIndex()
        root['RoomBlocking']['Indexes']['RoomBlockings'] = OOBTree()


@since('0.98-rc2')
def runReservationNotificationMigration(dbi, withRBDB, prevVersion):
    """
    Migrate the reservation notification system.
    """
    if not withRBDB:
        return

    # Delete old start end notification data
    for i, resv in enumerate(CrossLocationQueries.getReservations()):
        if hasattr(resv, '_startEndNotification'):
            resv._startEndNotification = None
        if i % 1000 == 0:
            DALManager.commit()
    # Create start notification task
    Client().enqueue(RoomReservationTask(rrule.HOURLY, byminute=0, bysecond=0))
    DALManager.commit()


@since('0.98b2')
def runLangToGB(dbi, withRBDB, prevVersion):
    """
    Replacing en_US with en_GB.
    """
    avatars = AvatarHolder().getList()
    for av in avatars:
        if av.getLang() == "en_US":
            av.setLang("en_GB")


@since('0.98b2')
def runMakoMigration(dbi, withRBDB, prevVersion):
    """
    Installing new TPLs for meeting/lecture styles
    """
    info = HelperMaKaCInfo().getMaKaCInfoInstance()
    sm = info.getStyleManager()
    try:
        del sm._stylesheets
    except:
        pass
    for lid in ['meeting', 'simple_event', 'conference']:
        l = sm._eventStylesheets[lid]
        if 'it' in l:
            l.remove('it')
        if 'administrative3' in l:
            l.remove('administrative3')
        sm._eventStylesheets[lid] = l
    styles = sm.getStyles()
    styles['xml'] = ('xml','XML.xsl',None)
    sm.setStyles(styles)


@since('0.98b2')
def runPluginOptionsRoomGUIDs(dbi, withRBDB, prevVersion):
    """
    Modifying Room GUIDs
    """
    if not withRBDB:
        return

    ph = PluginsHolder()
    for pluginName, roomsOpt in [('WebcastRequest', 'webcastCapableRooms'),
                                 ('RecordingRequest', 'recordingCapableRooms')]:
        opt = ph.getPluginType('Collaboration').getPlugin(pluginName).getOption(roomsOpt)
        newValue = []
        for name in opt.getValue():
            loc, name = name.split(':')
            room = CrossLocationQueries.getRooms(location=loc, roomName=name)
            if room:
                newValue.append(str(room.guid))
        opt.setValue(newValue)


def runMigration(withRBDB=False, prevVersion=parse_version(__version__)):

    print "\nExecuting migration...\n"

    dbi = DBMgr.getInstance()

    # go from older to newer version and execute corresponding tasks
    for version, task in MIGRATION_TASKS:
        if parse_version(version) > prevVersion:
            print console.colored("->", 'green', attrs=['bold']), \
                  task.__doc__.replace('\n', '').strip(),
            print console.colored("(%s)" % version, 'yellow')
            dbi.startRequest()
            if withRBDB:
                DALManager.connect()

            task(dbi, withRBDB, prevVersion)

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
    parser.add_argument('--prev-version', dest='prevVersion', help='Previous version of Indico (used by DB)', default=__version__)

    args = parser.parse_args()

    if console.yesno("Are you sure you want to execute the "
                     "migration now?"):
        try:
            return runMigration(withRBDB=args.useRBDB, prevVersion=parse_version(args.prevVersion))
        except:
            print console.colored("\nMigration failed! DB may be in "
                                  " an inconsistent state:", 'red', attrs=['bold'])
            print console.colored(traceback.format_exc(), 'red')
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())

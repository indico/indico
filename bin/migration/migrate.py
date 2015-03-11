# -*- coding: utf-8 -*-
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
Migration script

NOTE: Methods should be specified in order of execution, since @since adds them to
the task list in the order it is called.
"""


import sys, traceback, argparse
import bcrypt
from BTrees.OOBTree import OOTreeSet, OOBTree
from BTrees.IOBTree import IOBTree
from dateutil import rrule
from pkg_resources import parse_version
from collections import defaultdict

from MaKaC import __version__
from MaKaC.common.indexes import IndexesHolder, CategoryDayIndex, CalendarDayIndex
from indico.core.db import DBMgr
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.common.Counter import Counter
from indico.core.config import Config
from MaKaC.conference import ConferenceHolder, CategoryManager, Conference, CustomLocation, CustomRoom
from MaKaC.common.timerExec import HelperTaskList
from MaKaC.plugins.base import Plugin, PluginType, PluginsHolder
from MaKaC.registration import RegistrantSession, RegistrationSession
from MaKaC.plugins.RoomBooking.default.dalManager import DALManager
from MaKaC.plugins.RoomBooking.default.room import Room
from MaKaC.plugins.RoomBooking.tasks import RoomReservationTask
from MaKaC.plugins.Collaboration.Vidyo.common import VidyoTools
from MaKaC.plugins.Collaboration import urlHandlers
from MaKaC.webinterface import displayMgr
from MaKaC.authentication.LocalAuthentication import LocalAuthenticator, LocalIdentity
from MaKaC.authentication.LDAPAuthentication import LDAPIdentity, LDAPAuthenticator
from MaKaC.user import AvatarHolder
from MaKaC.rb_location import CrossLocationQueries
from MaKaC.review import AbstractField

from indico.core.index import Catalog
from indico.core.db.event import SupportInfo
from indico.ext import livesync
from indico.util import console, i18n
from indico.modules.scheduler.tasks import AlarmTask
from indico.modules.scheduler.tasks.periodic import FoundationSyncTask, CategoryStatisticsUpdaterTask
from indico.modules.scheduler.tasks.suggestions import CategorySuggestionTask
from indico.modules import ModuleHolder
from indico.util.redis import avatar_links
from indico.util.redis import client as redis_client
from indico.util.string import fix_broken_string

from indico.modules.scheduler import Client


MIGRATION_TASKS = []

i18n.setLocale('en_GB')


class ControlledExit(Exception):
    pass


def since(version, always=False, never=False):
    def _since(f):
        if not f.__doc__:
            raise ValueError('Function {0} has no docstring'.format(f.__name__))
        MIGRATION_TASKS.append((version, f, always, never))
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
def pluginMigration(dbi, withRBDB, prevVersion):
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


@since('0.97', always=True)
def pluginReload(dbi, withRBDB, prevVersion):
    """
    Reloading all plugins
    """
    PluginsHolder().reloadAllPlugins()
    dbi.commit()
    if withRBDB:
        DALManager.commit()


@since('0.98b')
def categoryACMigration(dbi, withRBDB, prevVersion):
    """
    Fixing AccessController for categories
    """
    for categ in CategoryManager()._getIdx().itervalues():
        _fixAccessController(categ)
        dbi.commit()


@since('0.98b2')
def conferenceMigration(dbi, withRBDB, prevVersion):
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
def taskMigration(dbi, withRBDB, prevVersion):
    """
    Migrating database tasks from the old format to the new one
    """

    c = Client()

    for t in HelperTaskList().getTaskListInstance().getTasks():
        for obj in t.listObj.values():
            print console.colored("   * %s" % obj.__class__.__name__, 'blue')
            if obj.__class__.__name__ == 'OfflineWebsiteCreator':
                continue
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
                print console.colored("WARNING: Unknown task type!", 'yellow')

    if withRBDB:
        DALManager.commit()
    dbi.commit()


@since('0.98b')
def categoryConfDictToTreeSet(dbi, withRBDB, prevVersion):
    """
    Replacing the conference dictionary in the Category objects by a OOTreeSet.
    """
    for categ in CategoryManager()._getIdx().itervalues():
        categ.conferencesBackup = categ.conferences.values()
        categ.conferences = OOTreeSet(categ.conferences.itervalues())
        if len(categ.conferences) != len(categ.conferencesBackup):
            print "Problem migrating conf dict to tree set: %s" % categ.getId()


@since('0.98b')
def categoryDateIndexMigration(dbi, withRBDB, prevVersion):
    """
    Replacing category date indexes.
    """
    if "backupCategoryDate" not in IndexesHolder()._getIdx():
        categoryDate = IndexesHolder().getIndex("categoryDate")
        IndexesHolder()._getIdx()["backupCategoryDate"] = categoryDate
        newIdx = CategoryDayIndex()
        newIdx.buildIndex(dbi)
        IndexesHolder()._getIdx()["categoryDate"] = newIdx
    else:
        print """categoryDateIndexMigration: new categoryDate index has """ \
        """NOT been generated because the index backup already exists.

If you still want to regenerate it, please, do it manually using """ \
        """bin/migration/CategoryDate.py"""


@since('0.98.1')
def categoryDateIndexWithoutVisibility(dbi, withRBDB, prevVersion):
    """
    Create category date index without visibility.
    """
    IndexesHolder()._getIdx()['categoryDate']._useVisibility = True
    if 'categoryDateAll' not in IndexesHolder()._getIdx():
        newIdx = CategoryDayIndex(visibility=False)
        IndexesHolder()._getIdx()['categoryDateAll'] = newIdx
        newIdx.buildIndex(dbi)


@since('0.98b', always=True)
def catalogMigration(dbi, withRBDB, prevVersion):
    """
    Initializing/updating index catalog
    """
    PluginsHolder().reloadAllPlugins(disable_if_broken=False)
    skip = False

    for plugin in (p for p in PluginsHolder().getList() if isinstance(p, Plugin) or isinstance(p, PluginType)):
        if plugin.isActive() and not plugin.isUsable():
            print console.colored(
                "\r  Plugin '{0}' is going to be disabled: {1}".format(
                    plugin.getName(),
                    plugin.getNotUsableReason()
                ), 'yellow')
            skip = True

    if skip and not console.yesno('\r  Do you want to continue the migration anyway?'):
        raise ControlledExit()

    Catalog.updateDB(dbi=dbi)


@since('0.98b2')
def roomBlockingInit(dbi, withRBDB, prevVersion):
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

@since('0.98.1')
def runRoomDayIndexInit(dbi, withRBDB, prevVersion):
    """
    Initializing room+day => reservation index.
    """
    if not withRBDB:
        return

    root = DALManager().getRoot()
    if not root.has_key('RoomDayReservationsIndex'):
        root['RoomDayReservationsIndex'] = OOBTree()
        for i, resv in enumerate(CrossLocationQueries.getReservations()):
            resv._addToRoomDayReservationsIndex()
            if i % 1000 == 0:
                DALManager.commit()
        DALManager.commit()

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
def langToGB(dbi, withRBDB, prevVersion):
    """
    Replacing en_US with en_GB.
    """
    avatars = AvatarHolder().getList()
    for av in avatars:
        if av.getLang() == "en_US":
            av.setLang("en_GB")


@since('0.98b2')
def makoMigration(dbi, withRBDB, prevVersion):
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
def pluginOptionsRoomGUIDs(dbi, withRBDB, prevVersion):
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


@since('0.98.1')
def slotLocationMigration(dbi, withRBDB, prevVersion):
    """
    Add missing location info to slots of a session that contains location or room
    """

    ch = ConferenceHolder()
    i = 0

    for (level, obj) in console.conferenceHolderIterator(ch, deepness='event'):
        for session in obj.getSessionList():
            for slot in session.getSlotList():
                sessionLoc = session.getOwnLocation()
                sessionRoom = session.getOwnRoom()
                if (sessionRoom is not None or sessionLoc is not None) and \
                    (slot.getOwnRoom() is None and slot.getOwnLocation() is None):
                    if sessionLoc:
                        loc = CustomLocation()
                        slot.setLocation(loc)
                        loc.setName(sessionLoc.getName())
                        loc.setAddress(sessionLoc.getAddress())
                    if sessionRoom:
                        r = CustomRoom()
                        slot.setRoom(r)
                        r.setName(sessionRoom.getName())
                        if sessionLoc and withRBDB:
                            r.retrieveFullName(sessionLoc.getName())
        if i%1000 == 999:
            dbi.commit()
        i+=1
    dbi.commit()


@since('0.98.3')
def collaborationRequestIndexCreate(dbi, withRBDB, prevVersion):
    """
    Creating new "All Requests" index
    """

    collab_plugin = PluginsHolder().getPluginType('Collaboration')

    if not collab_plugin.isUsable():
        print console.colored('  Collaboration plugin not usable - jumping task', 'yellow')
        return

    elif not collab_plugin.isActive():
        print console.colored('  Collaboration plugin not active - jumping task', 'blue')
        return

    ci = IndexesHolder().getById('collaboration')
    ci.indexAll(index_names=['All Requests'], dbi=dbi)
    dbi.commit()


@since('0.99')
def chatroomIndexMigration(dbi, withRBDB, prevVersion):
    """
    Migrating Chat Room index to new structure
    """

    # The structure of the indexes is such that for each one self._data
    #    is a BTree and each node is referenced by the IndexBy___ designation,
    #    where ___ is the ID in question. Each node is then a TreeSet of
    #    ChatRoom or XMPPChatRoom objects originally orderded by ID, we need
    #    this to be ordered by title for effective searching / querying.
    #   The __cmp__ method has been altered to accommodate this new format,
    #    take each subnode, iterate through saving the current objects, clear the
    #    index and reinsert them - they will now be in the correct order.

    from MaKaC.plugins.InstantMessaging.indexes import IndexByUser, IndexByConf, IndexByCRName, IndexByID

    im_plugin = PluginsHolder().getPluginType('InstantMessaging')

    if not im_plugin.isUsable():
        print console.colored('  IM plugin not usable - jumping task', 'yellow')
        return

    try:
        for idx in [IndexByUser(), IndexByConf(), IndexByCRName()]:
            tmp_idx = defaultdict(list)
            print console.colored("  * Index: " + str(idx), 'blue')

            for key, node in idx._data.iteritems():
                for leaf in node:
                    tmp_idx[key].append(leaf)

            # reset index
            idx._data.clear()

            for accum, rooms in tmp_idx.iteritems():
                for room in rooms:
                    # Specific handling as IndexByUser & IndexByConf have different
                    # arguements for tree insertion.
                    if isinstance(idx, IndexByUser) or isinstance(idx, IndexByConf):
                        idx.index(str(accum), room)
                    else:
                        idx.index(room)

        print console.colored("\tAll indexes have now been re-indexed and committed to the DB.", 'green')
    except:
        dbi.abort()
        print console.colored("Process failed, ended abruptly, changes not committed.", 'red')
        raise


@since('0.99')
def timedLinkedEventListRemoval(dbi, withRBDB, prevVersion):
    """
    Removing TimedLinkedEvents
    """
    i = 0
    for uid, user in AvatarHolder()._getIdx().iteritems():
        if hasattr(user, 'timedLinkedEvents'):
            del user.timedLinkedEvents
        i += 1
        if i % 100 == 0:
            dbi.commit()

@since('1.0')
def ip_based_acl(dbi, withRBDB, prevVersion):
    """
    Moving from OAI Private Harvesting to a more general IP-based ACL.
    """
    from MaKaC.common.info import IPBasedACLMgr
    minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
    ip_set = set(minfo._oaiPrivateHarvesterList)
    ip_acl_mgr = minfo._ip_based_acl_mgr = IPBasedACLMgr()
    ip_acl_mgr._full_access_acl = ip_set
    dbi.commit()

@since('1.0')
def removeOldCSSTemplates(dbi, withRBDB, prevVersion):
    """
    Removing old CSS Templates from events
    """

    mod = ModuleHolder().getById('cssTpls')

    try:
        del mod._cssTpls['template1.css']
    except KeyError, e:
        print 'info: %s'%e
    try:
        del mod._cssTpls['template2.css']
    except KeyError, e:
        print 'info: %s'%e
    try:
        del mod._cssTpls['top_menu.css']
    except KeyError, e:
        print 'info: %s'%e

    mod._p_changed = 1
    dbi.commit()

@since('1.0')
def conferenceMigration1_0(dbi, withRBDB, prevVersion):
    """
    Tasks: 1. Moving support info fields from conference to a dedicated class
           2. Update non inherited children list
           3. Update Vidyo indexes
    """

    def _updateMaterial(obj):
        for material in obj.getAllMaterialList(sort=False):
            material.getAccessController().setNonInheritingChildren(set())
            if material.getAccessController().getAccessProtectionLevel() != 0:
                material.notify_protection_to_owner(material)
            for resource in material.getResourceList(sort=False):
                if resource.getAccessController().getAccessProtectionLevel() != 0:
                    resource.notify_protection_to_owner()

    def updateSupport(conf):
        #################################################################
        #Moving support info fields from conference to a dedicated class:
        #################################################################

        dMgr = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(conf)
        caption = email = telephone = ""

        if hasattr(dMgr, "_supportEmailCaption"):
            caption = dMgr._supportEmailCaption
            del dMgr._supportEmailCaption
        if hasattr(conf, "_supportEmail"):
            email = conf._supportEmail
            del conf._supportEmail

        supportInfo = SupportInfo(conf, caption, email, telephone)
        conf.setSupportInfo(supportInfo)

    def updateNonInheritedChildren (conf):
        ####################################
        #Update non inherited children list:
        ####################################

        conf.getAccessController().setNonInheritingChildren(set())
        _updateMaterial(conf)

        for session in conf.getSessionList():
            session.getAccessController().setNonInheritingChildren(set())
            if session.getAccessController().getAccessProtectionLevel() != 0:
                session.notify_protection_to_owner(session)
            _updateMaterial(session)
        for contrib in conf.getContributionList():
            contrib.getAccessController().setNonInheritingChildren(set())
            if contrib.getAccessController().getAccessProtectionLevel() != 0:
                contrib.notify_protection_to_owner(contrib)
            _updateMaterial(contrib)
            for subContrib in contrib.getSubContributionList():
                _updateMaterial(subContrib)

    def updateVidyoIndex(conf, endDateIndex, vidyoRoomIndex):
        ####################################
        #Update vidyo indexes:
        ####################################
        csbm = getattr(conf, "_CSBookingManager", None)
        if csbm is None:
            return
        for booking in csbm.getBookingList():
            if booking.getType() == "Vidyo" and booking.isCreated():
                endDateIndex.indexBooking(booking)
                vidyoRoomIndex.indexBooking(booking)

    ph = PluginsHolder()
    collaboration_pt = ph.getPluginType("Collaboration")
    vidyoPluginActive = collaboration_pt.isActive() and collaboration_pt.getPlugin("Vidyo").isActive()
    if vidyoPluginActive:
        endDateIndex = VidyoTools.getEventEndDateIndex()
        vidyoRoomIndex = VidyoTools.getIndexByVidyoRoom()
        endDateIndex.clear()
        vidyoRoomIndex.clear()

    ch = ConferenceHolder()
    i = 0

    for (__, conf) in console.conferenceHolderIterator(ch, deepness='event'):

        updateSupport(conf)
        updateNonInheritedChildren(conf)
        if vidyoPluginActive:
            updateVidyoIndex(conf, endDateIndex, vidyoRoomIndex)

        if i % 10000 == 9999:
            dbi.commit()
        i += 1
    dbi.commit()


@since('1.0')
def changeVidyoRoomNames(dbi, withRBDB, prevVersion):
    """
    Changing Vidyo Room Names
    """
    ph = PluginsHolder()
    collaboration_pt = ph.getPluginType("Collaboration")
    if not collaboration_pt.isActive() or not collaboration_pt.getPlugin("Vidyo").isActive():
        return
    i = 0
    for booking in VidyoTools.getIndexByVidyoRoom().itervalues():
        if hasattr(booking, '_originalConferenceId'):
            roomName = booking.getBookingParamByName("roomName") + '_indico_' + booking._originalConferenceId
            booking._bookingParams["roomName"] = roomName
            del booking._originalConferenceId
        i += 1
        if i % 10000 == 0:
            dbi.commit()
    dbi.commit()


@since('1.1')
def indexConferenceTitle(dbi, withRBDB, prevVersion):
    """
    Indexing Conference Title
    """
    ch = ConferenceHolder()
    nameIdx = IndexesHolder().getIndex('conferenceTitle')
    i = 0

    for (__, conf) in console.conferenceHolderIterator(ch, deepness='event'):
        nameIdx.index(conf.getId(), conf.getTitle().decode('utf-8'))
        i += 1
        if i % 10000 == 0:
            dbi.commit()


@since('1.1')
def convertLinkedTo(dbi, withRBDB, prevVersion):
    """Convert Avatar.linkedTo structure to use OOTreeSets
       and import linkedTo information into Redis (if enabled)"""
    print 'Note: Some links might point to broken objects which will be skipped automatically.'

    use_redis = Config.getInstance().getRedisConnectionURL()

    if use_redis:
        pipe = redis_client.pipeline(transaction=False)

    for i, avatar in enumerate(AvatarHolder()._getIdx().itervalues()):
        avatar.updateLinkedTo()  # just in case some avatars do not have all fields
        linkedTo = avatar.linkedTo
        avatar.resetLinkedTo()  # nuke old links
        for field, data in avatar.linkedToMap.iteritems():
            for role in data['roles']:
                if not linkedTo[field][role]:
                    continue
                todo = set(linkedTo[field][role])
                # We have broken objects in the database which will fail in the getConference() call. If the current
                # object type has such a method call it on each object and skip it in case it raises an AttributeError
                if hasattr(linkedTo[field][role][0], 'getConference'):
                    for obj in linkedTo[field][role]:
                        try:
                            obj.getConference()
                        except AttributeError, e:
                            print '  \tSkipping broken object in %s/%s/%s: %r' % (avatar.getId(), field, role, obj)
                            todo.remove(obj)
                avatar.linkedTo[field][role].update(todo)
        if use_redis:
            avatar_links.init_links(avatar, client=pipe)
        if i % 1000 == 0:
            if use_redis:
                pipe.execute()
            dbi.commit()
        print '\r  %d' % i,
        sys.stdout.flush()
    print '\r  Done   '
    dbi.commit()


@since('1.1')
def redisLinkedTo(dbi, withRBDB, prevVersion):
    """Import linkedTo information into Redis"""
    if not Config.getInstance().getRedisConnectionURL():
        print console.colored("  Redis not configured, skipping", 'yellow')
        return

    with redis_client.pipeline(transaction=False) as pipe:
        for i, avatar in enumerate(AvatarHolder()._getIdx().itervalues()):
            avatar_links.init_links(avatar, client=pipe)
            if i % 1000 == 0:
                pipe.execute()
                dbi.sync()
            print '\r  %d' % i,
            sys.stdout.flush()
        pipe.execute()
    print '\r  Done   '


@since('1.2')
def addSuggestionsTask(dbi, withRBDB, prevVersion):
    """Add Category Suggestion Task to scheduler (Redis needed)"""
    if not Config.getInstance().getRedisConnectionURL():
        print console.colored("  Redis not configured, skipping", 'yellow')
        return
    task = CategorySuggestionTask(rrule.DAILY)
    client = Client()
    client.enqueue(task)
    dbi.commit()

@since('1.2')
def conferenceMigration1_2(dbi, withRBDB, prevVersion):
    """
    Tasks: 1. Removing Video Services from core
           2. Migrates old AbstractField to new AbstractField subclasses
           3. Add download e-ticket PDF link to the menu
    """

    def removeVideoServicesLinksFromCore(conf):
        """
        Video Services migration remove from core
        """

        # Update Menu Links
        menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(conf).getMenu()
        if menu:
            link = menu.getLinkByName("collaboration")
            if link:
                link.setURLHandler(urlHandlers.UHCollaborationDisplay)

    def updateAbstractFields(conf):
        """
        Migrates old AbstractField to new AbstractField subclasses
        """

        afm = conf.getAbstractMgr().getAbstractFieldsMgr()
        for index, field in enumerate(afm._fields):
            if field is not None:
                if type(field) != AbstractField:
                    continue  # Database already contains AbstractField objects created on v1.2.
                params = {}
                params["id"] = field._id
                params["type"] = field._type
                params["caption"] = field._caption
                params["isMandatory"] = field._isMandatory
                try:
                    params["maxLength"] = field._maxLength
                except:
                    pass
                try:
                    params["limitation"] = field._limitation
                except:
                    pass
                afm._fields[index] = AbstractField.makefield(params)
                afm._p_changed = 1
        # Delete all None items in the field list
        afm._fields = filter(None, afm._fields)

    cdmr = displayMgr.ConfDisplayMgrRegistery()
    ch = ConferenceHolder()
    i = 0

    for (__, conf) in console.conferenceHolderIterator(ch, deepness='event'):

        removeVideoServicesLinksFromCore(conf)
        updateAbstractFields(conf)
        # Add download e-ticket PDF link to the menu:
        _fixDefaultStyle(conf, cdmr)

        if i % 10000 == 9999:
            dbi.commit()
        i += 1
    dbi.commit()


@since('1.2')
def localIdentityMigration(dbi, withRBDB, prevVersion):
    """Generate the new password with a salt"""

    auth = LocalAuthenticator()
    total = len(auth.getList())
    for i, identity in enumerate(auth.getList()):
        print '\r  Processing %d/%d' % (i + 1, total),
        if not hasattr(identity, 'algorithm'):
            identity.setPassword(identity.password)
        if i % 1000 == 999:
            dbi.commit()
    print
    dbi.commit()


@since('1.2')
def removeNiceIdentities(dbi, withRBDB, prevVersion):
    """
    Remove the NiceIdentities from the avatars
    """

    for i, avatar in enumerate(AvatarHolder().getList()):
        for identity in avatar.getIdentityList()[:]:
            if not isinstance(identity, (LocalIdentity, LDAPIdentity)):
                avatar.removeIdentity(identity)
        if i % 100 == 99:
            dbi.commit()
    dbi.commit()


@since('1.2')
def lowercaseLDAPIdentities(dbi, withRBDB, prevVersion):
    """Convert all LDAP identities to lowercase"""
    auth = LDAPAuthenticator()
    total = len(auth.getList())
    idx = auth.getIdx()
    to_fix = set()
    for i, (key, identity) in enumerate(idx.iteritems(), 1):
        print '\r  Checking %d/%d' % (i, total),
        # getId() returns getLogin().lower()
        if key == identity.getId():
            continue
        to_fix.add((key, identity))

    print
    for i, (key, identity) in enumerate(to_fix, 1):
        print '\r  Fixing %d/%d' % (i, len(to_fix)),
        del idx[key]
        if identity.getId() in idx:
            assert identity.getId() == idx[identity.getId()].getId()
            continue
        idx[identity.getId()] = identity
        if i % 1000 == 0:
            dbi.commit()
    print
    dbi.commit()


@since('1.2')
def updateAvatarEmails(dbi, withRBDB, prevVersion):
    """
    Makes sure that all the secondary emails are lower case (otherwise it would be difficult to use indexes)
    """
    j = 0
    for i, avatar in enumerate(AvatarHolder()._getIdx().itervalues()):
        avatar.setSecondaryEmails(avatar.getSecondaryEmails())
        if j % 1000 == 999:
            dbi.commit()
        j += 1
    dbi.commit()


@since('1.2')
def fixIndexesEncoding(dbi, withRBDB, prevVersion):
    """
    Fix indexes encoding. They may be in unicode and they have to be encoded in utf-8
    """

    INDEXES = ["name", "surName", "organisation"]

    ih = IndexesHolder()
    for idx_name in INDEXES:
        idx = ih.getById(idx_name)
        words = idx._words
        for key in list(words):
            newKey = fix_broken_string(key)
            values = words[key]
            del words[key]
            words[newKey] = values
        idx.setIndex(words)
        dbi.commit()


def runMigration(withRBDB=False, prevVersion=parse_version(__version__),
                 specified=[], dry_run=False, run_from=None):

    global MIGRATION_TASKS

    if not dry_run:
        print "\nExecuting migration...\n"

        dbi = DBMgr.getInstance()

        print "Probing DB connection...",

        # probe DB connection
        dbi.startRequest()
        dbi.endRequest(False)

        print "DONE!\n"

    if run_from:
        try:
            mig_tasks_names = list(t.__name__ for (__, t, __, __) in MIGRATION_TASKS)
            mti = mig_tasks_names.index(run_from)
            MIGRATION_TASKS = MIGRATION_TASKS[mti:]
        except ValueError:
            print console.colored("The task {0} does not exist".format(run_from), 'red')
            return 1
    # go from older to newer version and execute corresponding tasks
    for version, task, always, never in MIGRATION_TASKS:
        if never and task.__name__ not in specified:
            continue
        if specified and task.__name__ not in specified:
            continue
        if parse_version(version) > prevVersion or always:
            print console.colored("#", 'green', attrs=['bold']), \
                task.__doc__.replace('\n', '').replace('  ', '').strip(),
            print console.colored("(%s)" % version, 'yellow')
            if dry_run:
                continue
            dbi.startRequest()
            if withRBDB:
                DALManager.connect()

            task(dbi, withRBDB, prevVersion)

            if withRBDB:
                DALManager.commit()
            dbi.endRequest()

            print console.colored("  DONE\n", 'green', attrs=['bold'])

    if not dry_run:
        print console.colored("Database Migration successful!\n",
                              'green', attrs=['bold'])


def main():
    """
    Main program cycle
    """

    print console.colored("""\nThis script will migrate your Indico DB to a new version. We recommend that
this operation be executed while the web server is down, in order to avoid
concurrency problems and DB conflicts.\n\n""", 'yellow')

    parser = argparse.ArgumentParser(description='Execute migration')
    parser.add_argument('--dry-run', '-n', dest='dry_run', action='store_true',
                        help='Only show which migration tasks would be executed')
    parser.add_argument('--with-rb', dest='useRBDB', action='store_true',
                        help='Use the Room Booking DB')
    parser.add_argument('--run-only', dest='specified', default='',
                        help='Specify which step(s) to run (comma-separated)')
    parser.add_argument('--run-from', dest='run_from', default='',
                        help='Specify FROM which step to run (inclusive)')
    parser.add_argument('--prev-version', dest='prevVersion', help='Previous version of Indico (used by DB)', default=__version__)
    parser.add_argument('--profile', dest='profile', help='Use profiling during the migration', action='store_true')

    args = parser.parse_args()

    if args.dry_run or console.yesno("Are you sure you want to execute the migration now?"):
        try:
            if args.profile:
                import profile, random, os
                proffilename = os.path.join(Config.getInstance().getTempDir(), "migration%s.prof" % str(random.random()))
                result = None
                profile.runctx("""result=runMigration(withRBDB=args.useRBDB,
                                  prevVersion=parse_version(args.prevVersion),
                                  specified=filter(lambda x: x, map(lambda x: x.strip(), args.specified.split(','))),
                                  run_from=args.run_from,
                                  dry_run=args.dry_run)""",
                                  globals(), locals(), proffilename)
                return result
            else:
                return runMigration(withRBDB=args.useRBDB,
                                    prevVersion=parse_version(args.prevVersion),
                                    specified=filter(lambda x: x, map(lambda x: x.strip(), args.specified.split(','))),
                                    run_from=args.run_from,
                                    dry_run=args.dry_run)
        except ControlledExit:
            return 1
        except (Exception, SystemExit, KeyboardInterrupt):
            print console.colored("\nMigration failed! DB may be in "
                                  " an inconsistent state:", 'red', attrs=['bold'])
            print console.colored(traceback.format_exc(), 'red')
            return -1
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())

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
## along with Indico; if not, see <http://www.gnu.org/licenses/>.

"""
Migration script

NOTE: Methods should be specified in order of execution, since @since adds them to
the task list in the order it is called.
"""

import argparse
import sys
import traceback

from dateutil import rrule
from pkg_resources import parse_version

from indico.core.config import Config
from indico.core.db import DBMgr
from indico.core.index import Catalog
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.tasks import OccurrenceNotifications
from indico.modules.scheduler.tasks import AlarmTask
from indico.modules.scheduler.tasks.suggestions import CategorySuggestionTask
from indico.modules.scheduler import Client
from indico.util import console, i18n
from indico.util.redis import avatar_links
from indico.util.redis import client as redis_client
from indico.util.string import fix_broken_string
from indico.web.flask.app import make_app
from MaKaC import __version__
from MaKaC.common.indexes import IndexesHolder
from MaKaC.conference import ConferenceHolder, CategoryManager
from MaKaC.plugins.base import PluginsHolder, Plugin, PluginType
from MaKaC.plugins.Collaboration import urlHandlers
from MaKaC.webinterface import displayMgr
from MaKaC.authentication.LocalAuthentication import LocalAuthenticator, LocalIdentity
from MaKaC.authentication.LDAPAuthentication import LDAPIdentity, LDAPAuthenticator
from MaKaC.user import AvatarHolder
from MaKaC.review import AbstractField


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


@since('0.0', always=True)
def pluginReload(dbi, prevVersion):
    """
    Reloading all plugins
    """
    PluginsHolder().reloadAllPlugins()
    dbi.commit()


@since('0.0', always=True)
def catalogMigration(dbi, prevVersion):
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


@since('1.1')
def convertLinkedTo(dbi, prevVersion):
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
def redisLinkedTo(dbi, prevVersion):
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
def addSuggestionsTask(dbi, prevVersion):
    """Add Category Suggestion Task to scheduler (Redis needed)"""
    if not Config.getInstance().getRedisConnectionURL():
        print console.colored("  Redis not configured, skipping", 'yellow')
        return
    task = CategorySuggestionTask(rrule.DAILY)
    client = Client()
    client.enqueue(task)
    dbi.commit()


@since('1.2')
def conferenceMigration1_2(dbi, prevVersion):
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
def localIdentityMigration(dbi, prevVersion):
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
def removeNiceIdentities(dbi, prevVersion):
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
def lowercaseLDAPIdentities(dbi, prevVersion):
    """Convert all LDAP identities to lowercase"""
    auth = LDAPAuthenticator()
    total = len(auth.getList())
    idx = auth.getIdx()
    for i, identity in enumerate(auth.getList()):
        print '\r  Processing %d/%d' % (i + 1, total),
        # getId() returns getLogin().lower()
        if identity.getLogin() == identity.getId() or identity.getLogin() not in idx:
            continue
        del idx[identity.getLogin()]
        assert identity.getId() not in idx
        idx[identity.getId()] = identity
        if i % 1000 == 999:
            dbi.commit()
    print
    dbi.commit()


@since('1.9')
def reindexCategoryNameAndConferenceTitle(dbi, prevVersion):
    """
    Indexing Conference Title with new WhooshTextIndex
    """
    IndexesHolder().removeById('conferenceTitle')
    IndexesHolder().removeById('categoryName')
    confTitleIdx = IndexesHolder().getIndex('conferenceTitle')
    categNameIdx = IndexesHolder().getIndex('categoryName')
    dbi.commit()

    confTitleIdx.clear()
    confTitleIdx.initialize(dbi, ConferenceHolder().itervalues())

    categNameIdx.clear()
    categNameIdx.initialize(dbi, CategoryManager().itervalues())


@since('1.2')
def updateAvatarEmails(dbi, prevVersion):
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
def fixIndexesEncoding(dbi, prevVersion):
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


@since('1.9')
def addOccurrenceNotificationsTask(dbi, prevVersion):
    """
    Add OccurrenceNotificationsTask to scheduler and remove old RoomReservationTask
    """
    scheduler_client = Client()
    scheduler_module = scheduler_client._schedMod
    old_tasks = []

    for _, task in scheduler_module.getWaitingQueue():
        if getattr(task, 'typeId', None) in {'RoomReservationTask', 'RoomReservationEndTask'}:
            old_tasks.append(task)
    for task in scheduler_module._runningList:
        if getattr(task, 'typeId', None) in {'RoomReservationTask', 'RoomReservationEndTask'}:
            old_tasks.append(task)
    for finished_task in scheduler_module._finishedIndex.values():
        task = finished_task._task if hasattr(finished_task, '_task') else finished_task
        if getattr(task, 'typeId', None) in {'RoomReservationTask', 'RoomReservationEndTask'}:
            scheduler_module._finishedIndex.unindex_obj(finished_task)
    for failed_task in scheduler_module._failedIndex.values():
        task = failed_task._task if hasattr(failed_task, '_task') else failed_task
        if getattr(task, 'typeId', None) in {'RoomReservationTask', 'RoomReservationEndTask'}:
            scheduler_module._failedIndex.unindex_obj(failed_task)
    for task in old_tasks:
        scheduler_client.dequeue(task)

    scheduler_client.enqueue(OccurrenceNotifications(rrule.HOURLY, byminute=0, bysecond=0))
    dbi.commit()


@since('1.9')
def updatePluginSettingsNewRB(dbi, prevVersion):
    """Migrate plugin settings to be compatible with the new RB module"""
    ph = PluginsHolder()
    # Custom attributes are now loercase-with-dashes internally
    opt = ph.getPluginType('Collaboration').getPlugin('CERNMCU').getOption('H323_IP_att_name')
    if opt.getValue() == 'H323 IP':
        opt.setValue('h323-ip')
    # Replace room GUIDs with plain room IDs
    for plugin_name, rooms_opt in [('WebcastRequest', 'webcastCapableRooms'),
                                   ('RecordingRequest', 'recordingCapableRooms')]:
        opt = ph.getPluginType('Collaboration').getPlugin(plugin_name).getOption(rooms_opt)
        room_ids = []
        for room_id in opt.getValue():
            if isinstance(room_id, basestring):
                room_id = int(room_id.split('|')[1].strip())
            if Room.get(room_id):
                room_ids.append(room_id)
        opt.setValue(room_ids)

    dbi.commit()


def runMigration(prevVersion=parse_version(__version__), specified=[], dry_run=False, run_from=None):

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

            task(dbi, prevVersion)

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
                profile.runctx("""result=runMigration(
                                  prevVersion=parse_version(args.prevVersion),
                                  specified=filter(lambda x: x, map(lambda x: x.strip(), args.specified.split(','))),
                                  run_from=args.run_from,
                                  dry_run=args.dry_run)""",
                                  globals(), locals(), proffilename)
                return result
            else:
                with make_app().app_context():
                    return runMigration(prevVersion=parse_version(args.prevVersion),
                                        specified=filter(None, map(str.strip, args.specified.split(','))),
                                        run_from=args.run_from,
                                        dry_run=args.dry_run)
        except ControlledExit:
            return 1
        except (Exception, SystemExit, KeyboardInterrupt):
            print console.colored("\nMigration failed! DB may be in an inconsistent state:", 'red', attrs=['bold'])
            print console.colored(traceback.format_exc(), 'red')
            return -1
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())

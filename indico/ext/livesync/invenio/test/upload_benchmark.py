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

import contextlib, csv, dateutil, os, tempfile, time
from indico.ext.livesync import SyncManager
from indico.ext.livesync.invenio.agent import InvenioBatchUploaderAgent
from indico.ext.livesync.tasks import LiveSyncUpdateTask

import logging
from indico.tests.util import TestZEOServer

from indico.core.db import DBMgr
from MaKaC.plugins import PluginsHolder
from MaKaC.conference import CategoryManager, DefaultConference
from MaKaC import user

from MaKaC.common.contextManager import ContextManager
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.authentication import AuthenticatorMgr

from indico.tests.python.unit.plugins import DummyObservable

results = {}
scenarios = []

FAKE_SERVICE_PORT = 12380


def runTests(host='localhost', port=FAKE_SERVICE_PORT,
             scenarios=[(2, 10)]):

    execTimes = []

    agent = InvenioBatchUploaderAgent('test1', 'test1', 'test',
                                      0, 'http://%s:%s' \
                                      % (host, port))

    ph = PluginsHolder()
    ph.reloadAllPlugins()
    ph.getPluginType('livesync').toggleActive()
    do = DummyObservable()

    do._notify('updateDBStructures', 'indico.ext.livesync',
                              None, None, None)

    sm = SyncManager.getDBInstance()

    sm.registerNewAgent(agent)

    cm = CategoryManager()

    avatar = user.Avatar()
    avatar.setName( "fake" )
    avatar.setSurName( "fake" )
    avatar.setOrganisation( "fake" )
    avatar.setLang( "en_GB" )
    avatar.setEmail( "fake@fake.fake" )

    #registering user
    ah = user.AvatarHolder()
    ah.add(avatar)

    #setting up the login info
    li = user.LoginInfo( "dummyuser", "dummyuser" )
    am = AuthenticatorMgr()
    userid = am.createIdentity( li, avatar, "Local" )
    am.add( userid )

    #activate the account
    avatar.activateAccount()

    #since the DB is empty, we have to add dummy user as admin
    minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
    al = minfo.getAdminList()
    al.grant( avatar )

    dummy = avatar

    ContextManager.destroy()

    HelperMaKaCInfo.getMaKaCInfoInstance().setDefaultConference(DefaultConference())

    cm.getRoot()

    do._notify('requestStarted')

    home = cm.getById('0')

    # execute code
    for nconf in range(0, 1000):
        conf = home.newConference(dummy)
        conf.setTitle('Test Conference %s' % nconf)

    do._notify('requestFinished')

    time.sleep(1)

    # params won't be used
    task = LiveSyncUpdateTask(dateutil.rrule.MINUTELY)

    for scen in scenarios:

        print "Scenario %s workers, size = %s " % scen,

        # configure scenario
        InvenioBatchUploaderAgent.NUM_WORKERS = scen[0]
        InvenioBatchUploaderAgent.BATCH_SIZE = scen[1]

        ts = time.time()
        # just run it
        task.run()

        te = time.time()
        execTimes.append(te - ts)

        print "%s" % (te - ts)

        sm._track._pointers['test1'] = None

    for i in range(0, len(execTimes)):
        results[scenarios[i]] = execTimes[i]


def main():

    global scenarios, results

    #logger = logging.getLogger('')
    #handler = logging.StreamHandler()

    #logger.addHandler(handler)
    #logger.setLevel(logging.DEBUG)

    dirpath = tempfile.mkdtemp()

    server = TestZEOServer(12355, os.path.join(dirpath, 'data.fs'),
                           'localhost')
    server.start()

    DBMgr.setInstance(DBMgr(hostname='localhost', port=12355))

    scenarios = list((nworkers, sbatch) for nworkers in range(1, 10) \
                     for sbatch in range(100, 1100, 100))

    dbi = DBMgr.getInstance()
    dbi.startRequest()

    runTests('pcuds86.cern.ch', 80, scenarios)

    dbi.abort()

    server.shutdown()
    DBMgr.setInstance(None)

    with open('/tmp/buploader.csv', 'w') as f:
        csvfile = csv.writer(f)

        for params, result in results.iteritems():
            csvfile.writerow(list(params) + [result])

if __name__ == '__main__':
    main()

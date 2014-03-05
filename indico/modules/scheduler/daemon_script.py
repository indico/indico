#!/usr/bin/env python
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
This script starts an Indico Scheduler instance, forking it off as a background
process.
"""

import ConfigParser
import socket
import time, sys, os, argparse, logging, cmd, multiprocessing
from logging.handlers import SMTPHandler

from indico.modules.scheduler import Scheduler, SchedulerModule, Client, base

# legacy import
from indico.core.config import Config
from indico.core.db import DBMgr
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.plugins.RoomBooking.default.dalManager import DALManager


class SchedulerApp(object):

    def __init__(self, args):
        super(SchedulerApp, self).__init__()
        self.args = args
        config = Config.getInstance()
        worker = config.getWorkerName()

        cp = ConfigParser.ConfigParser()
        logging_conf_file = os.path.join(config.getConfigurationDir(), "logging.conf")
        cp.read(logging_conf_file)

        if cp.has_option('handler_smtp', 'args'):
            # get e-mail from logging config file
            log_mail = eval(cp.get('handler_smtp', 'args'))[2]
        else:
            log_mail = config.getSupportEmail()

        self.mailer = SMTPHandler(config.getSmtpServer(),
                                  'scheduler@%s' % worker,
                                  log_mail,
                                  "[indico_scheduler] Problem at %s" % worker)

        self.mailer.setLevel(logging.ERROR)

    def run(self):
        root_logger = logging.getLogger('')
        root_logger.addHandler(self.mailer)

        logger = logging.getLogger('daemon')
        try:
            Scheduler(multitask_mode = self.args.mode).run()
            return_val = 0
        except base.SchedulerQuitException:
            logger.info("Daemon shut down successfully")
            return_val = 0
        except:
            logger.exception("Daemon terminated for unknown reason ")
            return_val = -1
        finally:
            return return_val


def _setup(args):

    cfg = Config.getInstance()

    # logging setup
    handler = logging.handlers.TimedRotatingFileHandler(os.path.join(cfg.getLogDir(), 'scheduler.log'), 'midnight')
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(process)s %(name)s: %(levelname)-8s %(message)s"))

    if 'log' not in args.__dict__:
        args.log = 'INFO'

    level = getattr(logging, args.log)

    root_logger = logging.getLogger('')
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    if args.mode == 'processes':
        mp_logger = multiprocessing.get_logger()
        mp_logger.setLevel(level)
        mp_logger.addHandler(handler)


def _check_running(check_process=False):

    with DBMgr.getInstance().global_connection():
        status = Client().getStatus()

    if not check_process:
        return status['state']

    if status['pid'] is None:
        return False
    return os.path.isdir('/proc/{0}/'.format(status['pid']))


def _start(args):

    _setup(args)

    running = _check_running()

    if not args.force and running:
        raise Exception("The daemon seems to be already running (consider -f?)")
    if hasattr(args, 'standalone') and args.standalone:
        SchedulerApp(args).run()
    else:
        pid = os.fork()
        if pid:
            print pid
            return
        else:
            DBMgr.setInstance(None)
            SchedulerApp(args).run()

        return 0


def _stop(args):

    _setup(args)

    running = _check_running()

    if not args.force and not running:
        raise Exception("The daemon doesn't seem to be running (consider -f?)")

    dbi = DBMgr.getInstance()
    dbi.startRequest()
    c = Client()
    c.shutdown(msg = "Daemon script")
    dbi.commit()

    print "Waiting for death confirmation... "
    for i in range(0, 20):
        if not c.getStatus()['state']:
            break
        else:
            time.sleep(1)
            dbi.sync()
    else:
        print "FAILED!"

    print "DONE!"
    dbi.endRequest()


def _restart(args):
    with DBMgr.getInstance().global_connection():
        status = Client().getStatus()
    if status['hostname'] is not None and status['hostname'] != socket.getfqdn() and not args.force:
        raise Exception('The daemon is running on another machine ({0[hostname]}) (consider -f?)'.format(status))

    _stop(args)
    _start(args)


def _check(args):
    if not os.path.isdir('/proc'):
        raise Exception('This command only works on systems that have /proc/')

    with DBMgr.getInstance().global_connection():
        status = Client().getStatus()
        if status['hostname'] is not None and status['hostname'] != socket.getfqdn():
            print >>sys.stderr, 'The daemon is running on another machine ({0[hostname]})'.format(status)
            sys.exit(2)

        db_running = _check_running(False)
        os_running = _check_running(True)

        if not args.quiet:
            print >>sys.stderr, 'Database status: running={1}, host={0[hostname]}, pid={0[pid]}'.format(status, db_running)
            print >>sys.stderr, 'Process status:  running={0}'.format(os_running)

        if db_running and os_running:
            print status['pid']
            sys.exit(0)
        elif not db_running and not os_running:
            sys.exit(1)
        elif db_running and not os_running:
            if not args.quiet:
                print >>sys.stderr, 'Marking dead scheduler as not running'
            SchedulerModule.getDBInstance().setSchedulerRunningStatus(False)
            DBMgr.getInstance().commit()
            sys.exit(1)
        else:
            print >>sys.stderr, 'Unexpected state! Process is running, but scheduler is not marked as running'
            sys.exit(2)


def _show(args):

    dbi = DBMgr.getInstance()

    dbi.startRequest()
    c = Client()

    if args.field == "status":
        status = c.getStatus()

        if status['state']:
            print 'Scheduler is currently running on {0[hostname]} with pid {0[pid]}'.format(status)
        else:
            print 'Scheduler is currently NOT running'
        print """
Spooled commands: %(spooled)s

Tasks:
  - Waiting:  %(waiting)s
  - Running:  %(running)s
  - Failed:   %(failed)s
  - Finished: %(finished)s
""" % status
    elif args.field == "spool":

        for op, obj in c.getSpool():
            if op in ['add', 'del']:
                print "%s %s" % (op, obj)
            else:
                print op

    dbi.endRequest()


def _cmd(args):

    dbi = DBMgr.getInstance()

    dbi.startRequest()
    c = Client()

    if args.command == "clear_spool":
        print "%s operations removed" % c.clearSpool()

    dbi.endRequest()


def _run(args):
    _setup(args)

    formatter = logging.Formatter("%(asctime)s %(name)s - %(levelname)s %(filename)s:%(lineno)s: %(message)s")

    root = logging.getLogger('')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root.addHandler(handler)

    dbi = DBMgr.getInstance(max_disconnect_poll=40)
    dbi.startRequest()

    info = HelperMaKaCInfo.getMaKaCInfoInstance()
    useRBDB = info.getRoomBookingModuleActive()

    if useRBDB:
        DALManager.connect()

    sm = SchedulerModule.getDBInstance()
    t = sm.getTaskById(args.taskid)

    t.plugLogger(logging.getLogger('console.run/%s' % args.taskid))
    t.run()

    if useRBDB:
        DALManager.commit()
        DALManager.disconnect()
    dbi.endRequest()


def main():
    """
    """

    parser = argparse.ArgumentParser(description = sys.modules[__name__].__doc__)
    subparsers = parser.add_subparsers(help="the action to be performed")

    parser_start = subparsers.add_parser('start', help="start the daemon")
    parser_stop = subparsers.add_parser('stop', help="stop the daemon")
    parser_restart = subparsers.add_parser('restart', help="restart the daemon")
    parser_check = subparsers.add_parser('check', help="check and sync status")
    parser_show = subparsers.add_parser('show', help="show information")
    parser_cmd = subparsers.add_parser('cmd', help="execute a command")
    parser_run = subparsers.add_parser('run', help="run a task, from this process")

    parser.add_argument("-p", "--fork-processes", dest="mode",
                        action = "store_const", const='processes',
                        default = 'threads', required = False,
                        help = "spawns processes instead of threads")
    parser.add_argument("-f", "--force", dest="force",
                        action = "store_const", const=True,
                        default = False, required = False,
                        help = "ignores the information in the DB about scheduler "
                        "status")

    parser_start.add_argument("-s", "--standalone",
                        action = "store_const", const=True,
                        default = False, required = False,
                        help = "forces standalone mode -  process doesn't "
                        "go to background")

    parser_start.add_argument("--log",
                        type=str,
                        default = "INFO", required = False,
                        help = "set different logging mode")

    parser_start.set_defaults(func=_start)
    parser_stop.set_defaults(func=_stop)
    parser_restart.set_defaults(func=_restart)
    parser_check.set_defaults(func=_check)

    parser_check.add_argument('-q', '--quiet', dest='quiet', action='store_true', help='Suppress console output')

    parser_show.add_argument("field",
                        choices=['status', 'spool'],
                        type=str,
                        help = "information to be shown")

    parser_show.set_defaults(func = _show)

    parser_cmd.add_argument("command",
                        choices=['clear_spool'],
                        type=str,
                        help = "command to be executed")

    parser_cmd.set_defaults(func = _cmd)

    parser_run.add_argument("taskid",
                        type=int,
                        help = "task to be executed (id)")
    parser_run.set_defaults(func = _run)


    args = parser.parse_args()

    try:
        return args.func(args)
    except Exception, e:
        print e
        return -1


if __name__ == "__main__":
    main()

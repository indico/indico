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

"""
Simple utility script for livesync debugging and administration
"""

# system imports
import argparse, sys, traceback
from dateutil.rrule import MINUTELY

# indico legacy imports
from MaKaC.common import DBMgr

# indico imports
from indico.modules.scheduler import Client

# plugin imports
from indico.ext.livesync import SyncManager
from indico.ext.livesync.tasks import LiveSyncUpdateTask

def _yesno(message):
    inp = raw_input("%s [y/N] " % message)
    if inp == 'y' or inp == 'Y':
        return True
    else:
        return False


class ConsoleLiveSyncCommand(object):

    def run(self, args):

        self._dbi = DBMgr.getInstance()
        self._dbi.startRequest()

        self._sm = SyncManager.getDBInstance()
        self._track = self._sm.getTrack()

        result = self._run(args)

        self._dbi.endRequest(False)

        return result

class ListCommand(ConsoleLiveSyncCommand):
    """
    Lists entries in the MPT
    """

    def _run(self, args):

        if args.pid:
            it = self._track.pointerIterItems(args.pid, args.toTS)
        else:
            it = self._track._iter(args.fromTS, args.toTS)

        for ts, elem in it:
            print ts, elem

        return 0


class DestroyCommand(ConsoleLiveSyncCommand):
    """
    Completely resets the MPT. Please do not do this unless you know what you
    are doing...
    """

    def _run(self, args):
        if not _yesno("Are you sure you want to empty the MPT?"):
            return 1

        if not _yesno("Really... is this what you want?"):
            return 1

        self._sm.reset()
        self._dbi.commit()


class AgentCommand(ConsoleLiveSyncCommand):
    """
    Executes operations on agents
    """

    def _run(self, args):
        if args.command == "init_task":
            c = Client()
            task = LiveSyncUpdateTask(MINUTELY, interval = args.interval)
            c.enqueue(task)
            self._dbi.commit()



def main():
    parser = argparse.ArgumentParser(description = sys.modules[__name__].__doc__)
    subparsers = parser.add_subparsers(help="the action to be performed")

    parser_list = subparsers.add_parser("list", help = ListCommand.__doc__)
    parser_list.set_defaults(cmd = ListCommand)

    from_spec = parser_list.add_mutually_exclusive_group()

    from_spec.add_argument("--pointer", type = str, default = None,
                             dest="pid",
                             help = "pointer id (agent)" )

    from_spec.add_argument("--from", type = int, default = None,
                             dest="fromTS",
                             help = "start of timestamp interval" )

    parser_list.add_argument("--to", type = int, default = None,
                             dest="toTS",
                             help = "end of timestamp interval" )

    parser_destroy = subparsers.add_parser("destroy", help = DestroyCommand.__doc__)
    parser_destroy.set_defaults(cmd = DestroyCommand)

    parser_agent = subparsers.add_parser("agent", help = AgentCommand.__doc__)
    parser_agent.set_defaults(cmd = AgentCommand)

    parser_agent.add_argument("command",
                              choices=['init_task'],
                              type=str,
                              help = "command to be executed")

    parser_agent.add_argument("--interval", "-i", type = int, default = 15,
                              dest="interval",
                              help = "interval between runs" )

    args = parser.parse_args()

    try:
        return args.cmd().run(args)
    except Exception, e:
        traceback.print_exc()
        return -1

if __name__ == "__main__":
    sys.exit(main())

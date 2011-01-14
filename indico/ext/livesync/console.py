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
import argparse, sys, traceback, logging
from dateutil.rrule import MINUTELY

# indico legacy imports
from MaKaC.common import DBMgr
from MaKaC.conference import CategoryManager

# indico imports
from indico.modules.scheduler import Client

# plugin imports
from indico.ext.livesync import SyncManager
from indico.ext.livesync.tasks import LiveSyncUpdateTask
from indico.ext.livesync.agent import ThreadedRecordUploader

def _yesno(message):
    inp = raw_input("%s [y/N] " % message)
    if inp == 'y' or inp == 'Y':
        return True
    else:
        return False


class ConsoleLiveSyncCommand(object):

    def _run(self, args):
        """
        Should be overloaded
        """
        raise Exception("Unimplemented method")

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


def eventIterator(conference, tabs):
    for contrib in conference.getContributionList():
        yield contrib
        for scontrib in contrib.getSubContributionList():
            yield scontrib


def categoryIterator(category, tabs):

    clist = category.getSubCategoryList()
    i = 1
    for scateg in clist:
        print "%s[%d/%d] %s %s" % ('| ' * tabs + '|-', i, len(clist),
                                   scateg.getId(), scateg.getTitle())
        for e in categoryIterator(scateg, tabs + 1):
            yield e
        i += 1

    for conf in category.getConferenceList():
        yield conf
        for contrib in eventIterator(conf, tabs):
            yield contrib


def _basicStreamHandler():
    handler = logging.StreamHandler()
    logger = logging.getLogger('')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger

def _wrapper(iterator, operation):
    for elem in iterator:
        yield elem, operation

class AgentCommand(ConsoleLiveSyncCommand):
    """
    Executes operations on agents
    """

    def _run(self, args):

        if args.action == 'add_task':
            c = Client()
            task = LiveSyncUpdateTask(MINUTELY, interval=args.interval)
            c.enqueue(task)
        elif args.action == 'export':

            logger = _basicStreamHandler()

            if _yesno("This will export all the data to the remote service "
                      "using the agent (takes LONG). Are you sure?"):
                try:
                    agent = self._sm.getAllAgents()[args.agent]
                except KeyError:
                    raise Exception("Agent '%s' was not found!" % args.agent)

                root = CategoryManager().getById(0)
                agent._run(_wrapper(categoryIterator(root, 0),
                                    agent._creationState),
                           logger=logger)

        self._dbi.abort()


def main():
    """
    Main body of the script
    """
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)
    subparsers = parser.add_subparsers(help="the action to be performed")

    parser_list = subparsers.add_parser("list", help=ListCommand.__doc__)
    parser_list.set_defaults(cmd=ListCommand)

    from_spec = parser_list.add_mutually_exclusive_group()

    from_spec.add_argument("--pointer", type=str, default=None,
                             dest="pid",
                             help="pointer id (agent)" )

    from_spec.add_argument("--from", type=int, default=None,
                             dest="fromTS",
                             help="start of timestamp interval" )

    parser_list.add_argument("--to", type=int, default=None,
                             dest="toTS",
                             help="end of timestamp interval" )

    parser_destroy = subparsers.add_parser("destroy",
                                           help=DestroyCommand.__doc__)
    parser_destroy.set_defaults(cmd=DestroyCommand)

    parser_agent = subparsers.add_parser("agent", help=AgentCommand.__doc__)
    parser_agent.set_defaults(cmd=AgentCommand)

    parser_agent_subparsers = parser_agent.add_subparsers(help="agent action")

    parser_agent_add_task = parser_agent_subparsers.add_parser(
        "add_task",
        help="create a task that will periodically run all agents")
    parser_agent_add_task.set_defaults(action='add_task')

    parser_agent_export = parser_agent_subparsers.add_parser(
        "export",
        help="manually export records")
    parser_agent_export.set_defaults(action='export')

    parser_agent_add_task.add_argument("--interval", "-i", type=int,
                                       default=15,
                                       help="interval between runs" )

    ## parser_agent_export.add_argument("--from", "-f", type=int, default=15,
    ##                                  dest="fromTS",
    ##                                  metavar="TIMESTAMP",
    ##                                  help="timestamp to start at" )

    parser_agent_export.add_argument("--output", "-o", type=str,
                                     metavar="FILE",
                                     help="file to write to (offline export)" )

    parser_agent_export.add_argument("--agent", "-a", type=str,
                                     metavar="AGENT_ID",
                                     required=True,
                                     help="agent to export data with" )

    args = parser.parse_args()

    try:
        return args.cmd().run(args)
    except Exception:
        traceback.print_exc()
        return -1
    return 0

if __name__ == "__main__":
    sys.exit(main())

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

# indico legacy imports
from MaKaC.common import DBMgr

# plugin imports
from indico.ext.livesync import SyncManager


def _list(args):
    """
    Lists entries in the MPT
    """

    dbi = DBMgr.getInstance()

    dbi.startRequest()

    sm = SyncManager.getDBInstance()
    track = sm.getTrack()

    if args.pid:
        it = track.pointerIterItems(args.pid, args.toTS)
    else:
        it = track._iter(args.fromTS, args.toTS)

    for ts, elem in it:
        print ts, elem

    dbi.endRequest(False)

    return 0

def main():
    parser = argparse.ArgumentParser(description = sys.modules[__name__].__doc__)
    subparsers = parser.add_subparsers(help="the action to be performed")

    parser_list = subparsers.add_parser("list", help=_list.__doc__)
    parser_list.set_defaults(func = _list)

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


    args = parser.parse_args()

    try:
        return args.func(args)
    except Exception, e:
        traceback.print_exc()
        return -1

if __name__ == "__main__":
    sys.exit(main())

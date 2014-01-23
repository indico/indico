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

### Script for object revocation
import sys,os,re,getopt
from indico.core.db import DBMgr
from MaKaC.trashCan import TrashCanManager
from MaKaC.conference import Conference
from MaKaC.conference import Category
from MaKaC.conference import CategoryManager,ConferenceHolder
from MaKaC.common.contextManager import ContextManager

from indico.ext.livesync.components import RequestListenerContext



def usage():
    print "Usage: restore_meeting.py [-s|--show] [-c|--category= <category id>] [-m|--meeting= <meeting id>]"

def main(argv):
    category = -1
    meeting = -1
    show = 0

    try:
        opts, args = getopt.getopt(argv, "hm:c:s", ["help","meeting=","category=", "show"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-s","--show"):
            show = 1
        elif opt in ("-m","--meeting"):
            meeting = arg
        elif opt in ("-c","--category"):
            category = arg

    # Create database instance and open trashcan manager object
    DBMgr.getInstance().startRequest()
    t=TrashCanManager()
    conf = None
    if(show):
        for i in t.getList():
            if isinstance(i, Conference):
                if meeting != -1 and i.getId() == meeting:
                    print "[%s]%s"%(i.getId(),i.getTitle())
                elif meeting == -1:
                    print "[%s]%s"%(i.getId(),i.getTitle())
        sys.exit()

    if(meeting != -1 and category != -1):

        print "Meeting:%s"%meeting
        print "Category:%s" % category
        for i in t.getList():
            if isinstance(i,Conference):
                if i.getId() == meeting:
                    conf = i
                    break

        if conf:
            DBMgr.getInstance().sync()

            with RequestListenerContext():

                # Remove meeting from the TrashCanManager
                t.remove(conf)
                # Attach meeting to desired category
                cat = CategoryManager().getById(category)
                ConferenceHolder().add(conf)
                cat._addConference(conf)

                # Add Evaluation
                c = ConferenceHolder().getById(meeting)
                from MaKaC.evaluation import Evaluation
                c.setEvaluations([Evaluation(c)])

                # indexes
                c._notify('created', cat)

                for contrib in c.getContributionList():
                    contrib._notify('created', c)
        else:
            print "not found!"

        DBMgr.getInstance().endRequest()

    ContextManager.destroy()

if __name__ == "__main__":
    main(sys.argv[1:])

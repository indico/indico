#!/usr/bin/python
# -*- coding: utf-8 -*-
# ex: set tabstop=4 expandtab:
"""
removeNeverConfirmed.py

InDiCo user (Avatar+Identity) search-and-destroy tool for never
 confirmed account requests (spam).
# Adapted from removePasswords.py script

Copyright (C) 2012-2015 Dirk Hoffmann -CPPM-
All rights reserved. Use within the CTA consortium and other public research
projects in High Energy Physics permitted.
"""

# System imports
import sys
import getopt
from datetime import datetime

# Indico imports
from MaKaC.common.db import DBMgr
from MaKaC.user import AvatarHolder


def main():
    """
    Script for removal of never-confirmed Indico account requests.

    Usage: {0} [options]

    Valid options:
      -n/--dry-run  only list Avatars/Ids that would be removed
      -q/--quiet    remove all non-confirmed accounts with minimal output
      -h/--help     this help text
"""

    try:
        optlist, args = getopt.getopt(
            sys.argv[1:],
            'hn',
            ['help', 'dry-run'])
    except getopt.GetoptError as ex:
        print ex
        print main.__doc__.format(sys.argv[0])
        sys.exit(2)

    dryrun = False
    silent = False
    for o, a in optlist:
        if o in ("-n", "--dry-run"):
            dryrun = True
        if o in ("-q", "--quiet"):
            silent = True
        elif o in ("-h", "--help"):
            print main.__doc__.format(sys.argv[0])
            sys.exit(0)

    DBMgr.getInstance().startRequest()

    avh = AvatarHolder()
    removed = 0
    for avatar in avh.getValuesToList():
        idlist = avatar.getIdentityList()
        ids = "???"
        if len(idlist) > 0:
            ids = " ".join([i.getAuthenticatorTag() for i in idlist])
        else:
            ids = "no_login"
        notcon = avatar.isNotConfirmed()
        if not dryrun or notcon:
            print "{0:<40s} {1:6s} {2:3s} {3:9s} {4:4s} {5}".format(
                avatar.getFullName(),
                "Active" if avatar.isActivated() else "NotAct",
                "Dis" if avatar.isDisabled() else "Ena",
                "NotConfmd" if notcon else "Confirmed",
                avatar.getId(),
                ids
                )
        if notcon:
            if silent:
                avh.remove(avatar)
                removed += 1
                continue

            print " +", " / ".join(
                (
                    avatar.getOrganisation()[0:25],
                    avatar.getPhone(),
                    avatar.getEmail()
                ))
            print " + Last modified", datetime.fromtimestamp(avatar._p_mtime)
            if not dryrun and sys.stdin.isatty():
                ans = raw_input(
                    " Remove {0}? (No[|Yes|All|eXit]) >".format(
                        avatar.getFullName()
                    ))
                if ans.lower() in ("yes", "y"):
                    avh.remove(avatar)
                    removed += 1
                    print "REMOVED."
                elif ans.lower() in ("all", "a"):
                    silent = True
                    avh.remove(avatar)
                    removed += 1
                    print "REMOVED and going to remove ALL the following ..."
                elif ans.lower() in ("exit", "x"):
                    print "Committing previous removals and exiting ..."
                    break

    print removed, "account requests (Avatars) removed."

    DBMgr.getInstance().endRequest()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print "Interrupted."
        sys.exit(0)


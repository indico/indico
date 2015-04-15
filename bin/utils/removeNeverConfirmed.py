#!/usr/bin/python
# -*- coding: utf-8 -*-
# ex: set tabstop=4:
"""
removeNeverConfirmed.py
InDiCo user (Avatar+Identity) search-and-destroy tool for never 
 confirmed account requests (spam).
# Adapted from removePasswords.py script

Copyright (C) 2012-2015 Dirk Hoffmann -CPPM-
All rights reserved. Use within the CTA consortium and other public research
projects in High Energy Physics permitted.

$Id: indicoUserDump.py 6843 2014-06-12 23:33:57Z dirk $
"""


import sys, getopt

from MaKaC.common.db import DBMgr
from MaKaC.user import AvatarHolder


def main():

	try:
		optlist, args = getopt.getopt(sys.argv[1:],
			'hn',
			['help', 'dry-run'])
	except getopt.GetoptError as ex:
		print(ex)
		sys.exit(2)

	dryrun=False
	for o, a in optlist:
		if o in ("-n", "--dry-run"):
			dryrun = True
		elif o in ("-h", "--help"):
			print """Usage:
		-n/--dry-run  Only list Avatars/Ids that would be removed.
	"""
			sys.exit(0)


	DBMgr.getInstance().startRequest()

	ah = AvatarHolder()
	removed = 0
	for avatar in ah.getValuesToList():
		idlist = avatar.getIdentityList()
		ids="???"
		if (len(idlist) > 0): 
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
		if not dryrun and notcon:
			print " +", " / ".join(
				(
					avatar.getOrganisation()[0:25], 
					avatar.getPhone(),
					avatar.getEmail()
				))
			if sys.stdin.isatty():
				ans = raw_input(" Remove {0}? [yNxq] >".format(
						avatar.getFullName()
						))
				if ans.lower() in ("yes","y"):
					ah.remove(avatar)
					print "REMOVED."
				elif ans.lower() in ("exit", "x", "quit", "q"):
					print "Committing previous removals and exiting ..."
					break

	DBMgr.getInstance().endRequest()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
		print "Interrupted."
		sys.exit(0)



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
Simple utility script for recovering administrator privileges
"""

import argparse
import sys
import traceback
import logging
from getpass import getpass

from indico.core import db
from MaKaC.common import info
from MaKaC.user import AvatarHolder, Avatar, LoginInfo
from MaKaC.authentication import AuthenticatorMgr
from indico.util import console


class AdminCommand(object):

    def _run(self, args):
        """
        Should be overloaded
        """
        raise Exception("Unimplemented method")

    def run(self, args):
        self._dbi = db.DBMgr.getInstance()
        self._dbi.startRequest()
        result = self._run(args)
        self._dbi.endRequest(True)
        return result

    def printUserInfo(self, avatar, args_id=None):
        print ''
        if not avatar:
            raise Exception("User id '%s' does not exist" % args_id)
        if avatar.getId(): # If creating a user, there is no ID yet.
            print "User id: %s" % avatar.getId()
        print "User first name: %s" % avatar.getFirstName()
        print "User family name: %s" % avatar.getFamilyName()
        print "User email: %s" % avatar.getEmail()
        print "User affiliation: %s" % avatar.getAffiliation()
        print ''


class GrantCommand(AdminCommand):
    """
    Grant administrator privileges to user
    """
    def _run(self, args):
        avatar = AvatarHolder().getById(args.id)
        self.printUserInfo(avatar, args.id)
        if avatar.isAdmin():
            print "User seems to already has administrator privileges"
        if console.yesno("Are you sure to grant administrator privileges to this user?"):
            adminList = info.HelperMaKaCInfo.getMaKaCInfoInstance().getAdminList()
            adminList.grant(avatar)
            avatar.activateAccount()
            print "Administrator privileges granted successfully"
        return 0


class RevokeCommand(AdminCommand):
    """
    Revoke administrator privileges from user
    """
    def _run(self, args):
        avatar = AvatarHolder().getById(args.id)
        self.printUserInfo(avatar, args.id)
        if not avatar.isAdmin():
            print "User seems to has no administrator privileges"
        if console.yesno("Are you sure to revoke administrator privileges from this user?"):
            adminList = info.HelperMaKaCInfo.getMaKaCInfoInstance().getAdminList()
            adminList.revoke(avatar)
            print "Administrator privileges revoked successfully"
        return 0


class CreateCommand(AdminCommand):
    """
    Create new user and grant him administrator privileges
    """
    def _run(self, args):
        avatar = Avatar()

        name = raw_input("New administrator name: ").strip()
        surname = raw_input("New administrator surname: ").strip()
        organization = raw_input("New administrator organization: ").strip()
        email = raw_input("New administrator email: ").strip()
        login = raw_input("New administrator login: ").strip()
        password = getpass("New administrator password: ")
        password2 = getpass("Retype administrator password: ")
        if password != password2:
            raise Exception("Sorry, passwords do not match")

        avatar.setName(name)
        avatar.setSurName(surname)
        avatar.setOrganisation(organization)
        avatar.setLang("en_GB")
        avatar.setEmail(email)

        self.printUserInfo(avatar)

        if console.yesno("Are you sure to create and grant administrator privileges to this user?"):
            avatar.activateAccount()
            loginInfo = LoginInfo(login, password)
            authMgr = AuthenticatorMgr()
            userid = authMgr.createIdentity(loginInfo, avatar, "Local")
            authMgr.add(userid)
            adminList = info.HelperMaKaCInfo.getMaKaCInfoInstance().getAdminList()
            AvatarHolder().add(avatar)
            adminList.grant(avatar)
            print "New administrator created successfully with id: %s" % avatar.getId()


def main():
    """
    Main body of the script
    """
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)
    subparsers = parser.add_subparsers(help="The action to be performed")

    parser_grant = subparsers.add_parser("grant", help=GrantCommand.__doc__)
    parser_grant.set_defaults(cmd=GrantCommand)
    parser_grant.add_argument(type=str,
                              dest="id",
                              help="user id")

    parser_revoke = subparsers.add_parser("revoke", help=RevokeCommand.__doc__)
    parser_revoke.set_defaults(cmd=RevokeCommand)
    parser_revoke.add_argument(type=str,
                               dest="id",
                               help="user id")

    parser_create = subparsers.add_parser("create", help=CreateCommand.__doc__)
    parser_create.set_defaults(cmd=CreateCommand)

    args = parser.parse_args()

    try:
        return args.cmd().run(args)
    except Exception:
        traceback.print_exc()
        return -1
    return 0

if __name__ == "__main__":
    sys.exit(main())

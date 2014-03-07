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

import MaKaC.webinterface.rh.base as base
import MaKaC.webinterface.pages.wizard as wizard
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.user import AvatarHolder
from MaKaC.errors import AccessError
from MaKaC.i18n import _
import MaKaC.user as user
from MaKaC.authentication import AuthenticatorMgr
import MaKaC.webinterface.pages.signIn as signIn
from MaKaC.accessControl import AdminList

import re


class RHWizard(base.RHDisplayBaseProtected):

    def _validMail(self, email):
        if re.search("^[a-zA-Z][\w\.-]*[a-zA-Z0-9]@[a-zA-Z0-9][\w\.-]*[a-zA-Z0-9]\.[a-zA-Z][a-zA-Z\.]*[a-zA-Z]$",
                     email):
            return True
        return False

    def _checkProtection(self):
        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
        if minfo.getAdminList().getList() or AvatarHolder()._getIdx():
            raise AccessError

    def _checkParams(self, params):
        self._params = params
        base.RHDisplayBaseProtected._checkParams(self, params)
        self._save = params.get("save", "")
        self._accept = params.get("accept", "")
        self._activate = False
        self._params["msg"] = ""
        if self._save:
            self._activate = True
            br = "<br>"
            if not self._params.get("name", ""):
                self._params["msg"] += _("You must enter a name.")+br
                self._activate = False
            if not self._params.get("surName", ""):
                self._params["msg"] += _("You must enter a surname.")+br
                self._activate = False
            if not self._params.get("userEmail", ""):
                self._params["msg"] += _("You must enter an user email address.")+br
                self._activate = False
            elif not self._validMail(self._params.get("userEmail", "")):
                self._params["msg"] += _("You must enter a valid user email address")+br
                self._activate = False
            if not self._params.get("login", ""):
                self._params["msg"] += _("You must enter a login.")+br
                self._activate = False
            if not self._params.get("password", ""):
                self._params["msg"] += _("You must define a password.")+br
                self._activate = False
            if self._params.get("password", "") != self._params.get("passwordBis", ""):
                self._params["msg"] += _("You must enter the same password twice.")+br
                self._activate = False
            if not self._params.get("organisation", ""):
                self._params["msg"] += _("You must enter the name of your organisation.")+br
                self._activate = False
            if self._accept:
                if not self._params.get("instanceTrackingEmail", ""):
                    self._params["msg"] += _("You must enter an email address for Instance Tracking.")+br
                    self._activate = False
                elif not self._validMail(self._params.get("instanceTrackingEmail", "")):
                    self._params["msg"] += _("You must enter a valid email address for Instance Tracking")+br
                    self._activate = False

    def _process(self):
        if self._activate:
            # Creating new user
            ah = user.AvatarHolder()
            av = user.Avatar()
            authManager = AuthenticatorMgr()
            _UserUtils.setUserData(av, self._params)
            ah.add(av)
            li = user.LoginInfo(self._params["login"], self._params["password"])
            identity = authManager.createIdentity(li, av, "Local")
            authManager.add(identity)
            # Activating new account
            av.activateAccount()
            # Granting admin priviledges
            al = AdminList().getInstance()
            al.grant(av)
            # Configuring server's settings
            minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
            minfo.setOrganisation(self._params["organisation"])
            minfo.setTimezone(self._params["timezone"])
            minfo.setLang(self._params["lang"])
            minfo.setInstanceTrackingActive(bool(self._accept))
            if self._accept:
                minfo.setInstanceTrackingEmail(self._params["instanceTrackingEmail"])

            p = signIn.WPAccountActivated(self, av)
            return p.display()
        else:
            if self._params["msg"] != "":
                self._params["msg"] = "<table class=\"center\" bgcolor=\"gray\" style=\"text-align:left;\">" + \
                                      "<tr><td bgcolor=\"white\">\n<font size=\"+1\" color=\"red\"><b>" + \
                                      "{0}</b></font>\n</td></tr></table>".format(self._params["msg"])
            p = wizard.WPWizard(self, self._params)
            return p.display()


class _UserUtils:

    def setUserData(self, a, userData):
        a.setName(userData["name"])
        a.setSurName(userData["surName"])
        a.setOrganisation(userData["organisation"])
        a.setEmail(userData["userEmail"])
        ##################################
        # Fermi timezone awareness       #
        ##################################
        a.setTimezone(userData["timezone"])
        ##################################
        # Fermi timezone awareness(end)  #
        ##################################
        a.setLang(userData["lang"])
    setUserData = classmethod(setUserData)

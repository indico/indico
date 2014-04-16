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

from flask import request
from flask import render_template
from wtforms import Form, validators, TextField, PasswordField, BooleanField
from tzlocal import get_localzone

import MaKaC.webinterface.rh.base as base
import MaKaC.user as user
import MaKaC.webinterface.pages.signIn as signIn
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.user import AvatarHolder
from MaKaC.errors import AccessError, FormValuesError
from MaKaC.authentication import AuthenticatorMgr
from MaKaC.accessControl import AdminList
from MaKaC.i18n import _
from MaKaC.webinterface.common.timezones import TimezoneRegistry
from indico.web.forms.validators import UsedIfChecked
from indico.util.i18n import getLocaleDisplayNames


class RHInitialSetup(base.RHDisplayBaseProtected):

    def _setUserData(self, av):
        av.setName(self._params["name"])
        av.setSurName(self._params["surname"])
        av.setOrganisation(self._params["organisation"])
        av.setEmail(self._params["user_email"])
        av.setTimezone(self._params["timezone"])
        av.setLang(self._params["lang"])

    def _checkProtection(self):
        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
        if minfo.getAdminList().getList() or AvatarHolder()._getIdx():
            raise AccessError

    def _checkParams_GET(self):
        self._params = request.form.copy()

    def _checkParams_POST(self):
        self._params = request.form.copy()
        base.RHDisplayBaseProtected._checkParams(self, self._params)
        self._enable = self._params.get("enable", "")

    def _process_GET(self):
        tz = str(get_localzone())
        timezone_options = TimezoneRegistry.getShortSelectItemsHTML(tz)
        language_options = getLocaleDisplayNames()

        wvars = {'title': _('Initial Setup'),

                 'steps': [{'title': _('User creation'),
                            'description': [_('Insert here all the basic informations needed to ' +
                                              'create your admin account.'),
                                            _('You can update your account with all the secondary ' +
                                              'informations (like your address or phone number) in a ' +
                                              'second moment by accessing the account management ' +
                                              '(My Profile, Account Details).')]},
                           {'title': _('Server settings'),
                            'description': [_('Configure here your server settings.'),
                                            _('All the informations set here will also be used to fill ' +
                                              'your personal account information. To change these informations ' +
                                              'you can later head to Server Admin, General Settings (will change ' +
                                              'the server settings) or My Profile, Account Details (will change ' +
                                              'the account settings).')]},
                           {'title': _('Instance Tracking'),
                            'description': {'first': _('By enabling the Instance Tracking Terms you accept:'),
                                            'list': [_('sending anonymous statistic data to Indico@CERN;'),
                                                     _('receiving security warnings from the Indico team;'),
                                                     _('receiving a notification when a new version is released.')],
                                            'last': _('Please note that no private information will ever be sent to ' +
                                                      'Indico@CERN and that you will be able to change the Instance ' +
                                                      'Tracking settings anytime in the future (from Server ' +
                                                      'Admin, General Settings).')}}],

                 'next_step': _('Next step'),
                 'previous_step': _('Previous step'),
                 'submit': _('Submit'),

                 'name': {'label': _('First name'),
                          'tooltip': _('You must enter a name')},

                 'surname': {'label': _('Family name'),
                             'tooltip': _('You must enter a surname')},

                 'user_email': {'label': _('Email'),
                                'tooltip': {'missing': _('You must enter your user e-mail address'),
                                            'invalid': _('You must enter a valid e-mail address')}},

                 'login': {'label': _('Login'),
                           'tooltip': _('You must enter a login')},

                 'password': {'label': _('Password'),
                              'tooltip': _('You must define a password')},

                 'password_confirm': {'label': _('Password (again)'),
                                      'tooltip': _('You must enter the same password twice')},

                 'language': {'label': _('Language'),
                              'options': language_options},

                 'timezone': {'label': _('Timezone'),
                              'options': timezone_options},

                 'organisation': {'label': _('Organization'),
                                  'tooltip': _('You must enter the name of your organization')},

                 'enable': {'label': _('Enable')},

                 'it_email': {'label': _('Email'),
                              'tooltip': {'missing': _('You must enter an e-mail for Instance Tracking'),
                                          'invalid': _('You must enter a valid e-mail for Instance Tracking')}}}

        return render_template('initial_setup.html', **wvars)

    def _process_POST(self):
        setup_form = RegistrationForm(request.form)
        if not setup_form.validate():
            print setup_form.errors
            raise FormValuesError(_("Some fields are invalid. Please, correct them and submit the form again."))
        else:
            # Creating new user
            ah = user.AvatarHolder()
            av = user.Avatar()
            authManager = AuthenticatorMgr()
            self._setUserData(av)
            ah.add(av)
            li = user.LoginInfo(self._params["login"], self._params["password"].encode('UTF8'))
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
            minfo.setInstanceTrackingActive(bool(self._enable))
            if self._enable:
                minfo.setInstanceTrackingEmail(self._params["it_email"])

            p = signIn.WPAdminCreated(self, av)
            return p.display()


class RegistrationForm(Form):

    name = TextField('Name', [validators.Required()])
    surname = TextField('Surname', [validators.Required()])
    user_email = TextField('User Email Address', [validators.Required(), validators.Email()])
    login = TextField('Login', [validators.Required()])
    password = PasswordField('New Password', [validators.Required()])
    password_confirm = PasswordField('Repeat Password',
                                     [validators.EqualTo('password', message='Passwords must match')])
    organisation = TextField('Organisation', [validators.Required()])
    enable = BooleanField('Enable Instance Tracking')
    it_email = TextField('Instance Tracking Email Address',
                         [UsedIfChecked('enable'), validators.Required(), validators.Email()])

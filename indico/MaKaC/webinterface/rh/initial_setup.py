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

import requests
from flask import render_template, request, session
from wtforms import Form, validators, TextField, PasswordField, BooleanField
from tzlocal import get_localzone
from json import dumps

from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.pages import signIn
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.user import AvatarHolder, Avatar, LoginInfo
from MaKaC.errors import AccessError, FormValuesError
from MaKaC.authentication import AuthenticatorMgr
from MaKaC.accessControl import AdminList
from MaKaC.i18n import _
from MaKaC.webinterface.common.timezones import TimezoneRegistry
from indico.core.config import Config
from indico.web.forms.validators import UsedIfChecked
from indico.util.i18n import parseLocale, getLocaleDisplayNames


def register_instance(payload):
    minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
    url = Config.getInstance().getTrackerURL() + '/instance/'
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, data=dumps(payload), headers=headers).json()
        uuid = response['uuid']
    except (requests.exceptions.RequestException, ValueError, KeyError):
        minfo.setInstanceTrackingActive(False)
        return False
    else:
        minfo.setInstanceTrackingActive(True)
        minfo.setInstanceTrackingUUID(uuid)
    return True


def update_instance(uuid, payload):
    url = Config.getInstance().getTrackerURL() + '/instance/' + uuid
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.patch(url, data=dumps(payload), headers=headers)
        if response.status_code >= 400:
            raise requests.exceptions.RequestException
    except (requests.exceptions.RequestException):
        return False
    return True


class RHInitialSetup(RH):

    def _setUserData(self, av, setup_form):
        av.setName(setup_form.name.data)
        av.setSurName(setup_form.surname.data)
        av.setOrganisation(setup_form.organisation.data)
        av.setEmail(setup_form.user_email.data)
        av.setTimezone(setup_form.timezone.data)
        av.setLang(setup_form.language.data)

    def _checkProtection(self):
        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
        if minfo.getAdminList().getList() or AvatarHolder()._getIdx():
            raise AccessError

    def _checkParams_POST(self):
        self._enable = 'enable' in request.form

    def _process_GET(self):
        tz = str(get_localzone())
        timezone_options = TimezoneRegistry.getShortSelectItemsHTML(tz)
        language_options = getLocaleDisplayNames()
        for code in language_options:
            language_options.remove(code)
            language_options.append((code[0], code[1][0].upper() + code[1][1:]))
        sel_lang = session.lang
        locale = parseLocale(sel_lang)
        lang_name = locale.languages[locale.language].encode('utf-8')
        selected_language_name = lang_name[0].upper() + lang_name[1:]

        wvars = {'language_options': language_options,
                 'timezone_options': timezone_options,
                 'selected_language': sel_lang,
                 'selected_language_name': selected_language_name}

        return render_template('initial_setup.html', **wvars)

    def _process_POST(self):
        setup_form = InitialSetupForm(request.form)
        if not setup_form.validate():
            print setup_form.errors
            raise FormValuesError(_("Some fields are invalid. Please, correct them and submit the form again."))
        # Creating new user
        ah = AvatarHolder()
        av = Avatar()
        authManager = AuthenticatorMgr()
        self._setUserData(av, setup_form)
        ah.add(av)
        li = LoginInfo(setup_form.login.data, setup_form.password.data.encode('UTF8'))
        identity = authManager.createIdentity(li, av, "Local")
        authManager.add(identity)
        # Activating new account
        av.activateAccount()
        # Granting admin priviledges
        al = AdminList().getInstance()
        al.grant(av)
        # Configuring server's settings
        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
        minfo.setOrganisation(setup_form.organisation.data)
        minfo.setTimezone(setup_form.timezone.data)
        minfo.setLang(setup_form.language.data)
        if self._enable:
            minfo.setInstanceTrackingContact(setup_form.it_contact.data)
            minfo.setInstanceTrackingEmail(setup_form.it_email.data)
            # Posting a request to the server with the data
            payload = {'url': Config.getInstance().getBaseURL(),
                       'contact': setup_form.it_contact.data,
                       'email': setup_form.it_email.data,
                       'organisation': setup_form.organisation.data}
            register_instance(payload)

        p = signIn.WPAdminCreated(self, av)
        return p.display()


class InitialSetupForm(Form):
    name = TextField('Name', [validators.Required()])
    surname = TextField('Surname', [validators.Required()])
    user_email = TextField('User Email Address', [validators.Required(), validators.Email()])
    login = TextField('Login', [validators.Required()])
    password = PasswordField('New Password', [validators.Required()])
    password_confirm = PasswordField('Repeat Password',
                                     [validators.EqualTo('password', message='Passwords must match')])
    timezone = TextField('Timezone', [validators.Required()])
    language = TextField('Language', [validators.Required()])
    organisation = TextField('Organisation', [validators.Required()])
    enable = BooleanField('Enable Instance Tracking')
    it_email = TextField('Instance Tracking Email Address',
                         [UsedIfChecked('enable'), validators.Required(), validators.Email()])
    it_contact = TextField('Instance Tracking Email Address',
                           [UsedIfChecked('enable'), validators.Required()])

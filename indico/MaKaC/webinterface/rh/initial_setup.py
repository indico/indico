# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from operator import itemgetter

from flask import render_template, request, session
from pytz import common_timezones
from tzlocal import get_localzone
from wtforms import validators, TextField, SelectField, BooleanField
from wtforms.fields.html5 import EmailField

from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.rh import services
from MaKaC.webinterface.pages import signIn
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.errors import AccessError, FormValuesError

from indico.modules.auth.forms import LocalRegistrationForm
from indico.modules.users import User
from indico.util.i18n import _, get_all_locales, parse_locale
from indico.web.forms.validators import UsedIfChecked
from indico.web.forms.widgets import SwitchWidget


class RHInitialSetup(RH):

    def _setUserData(self, av, setup_form):
        av.setName(setup_form.name.data)
        av.setSurName(setup_form.surname.data)
        av.setOrganisation(setup_form.organisation.data)
        av.setEmail(setup_form.user_email.data)
        av.setTimezone(setup_form.timezone.data)
        av.setLang(setup_form.language.data)

    def _checkProtection(self):
        if User.query.count() > 0:
            raise AccessError

    def _checkParams_POST(self):
        self._enable = 'enable' in request.form

    def _process_GET(self):
        return render_template('initial_setup.html',
                               selected_lang_name=parse_locale(session.lang).language_name,
                               language_options=sorted(get_all_locales().items(), key=itemgetter(1)),
                               form=InitialSetupForm(timezone=str(get_localzone()), language=session.lang))

    def _process_POST(self):
        setup_form = InitialSetupForm(request.form)
        if not setup_form.validate():
            print setup_form.errors
            raise FormValuesError(_("Some fields are invalid. Please, correct them and submit the form again."))
        # Creating new user

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
            # Posting a request to the server with the data
            services.register_instance(setup_form.it_contact.data, setup_form.it_email.data)

        p = signIn.WPAdminCreated(self, av)
        return p.display()


class InitialSetupForm(LocalRegistrationForm):
    first_name = TextField('First Name', [validators.Required()])
    last_name = TextField('Last Name', [validators.Required()])
    email = EmailField(_('Email address'), [validators.Required()])
    timezone = SelectField('Timezone', [validators.Required()], choices=[(k, k) for k in common_timezones])
    language = SelectField('Language', [validators.Required()])
    affiliation = TextField('Organization', [validators.Required()])
    enable_tracking = BooleanField('Enable Instance Tracking', widget=SwitchWidget())
    contact_name = TextField('Contact Name',
                             [UsedIfChecked('enable'), validators.Required()])
    contact_email = EmailField('Contact Email Address',
                               [UsedIfChecked('enable'), validators.Required(), validators.Email()])

    def __init__(self, *args, **kwargs):
        super(InitialSetupForm, self).__init__(*args, **kwargs)
        self.language.choices = sorted(get_all_locales().items(), key=itemgetter(1))

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

import transaction
from operator import itemgetter

from flask import flash, redirect, render_template, request, session
from markupsafe import Markup
from wtforms import validators, TextField, SelectField, BooleanField
from wtforms.fields.html5 import EmailField

from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.rh import services
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.errors import AccessError, FormValuesError

from indico.core.config import Config
from indico.core.db import db
from indico.modules.auth import Identity, login_user
from indico.modules.auth.forms import LocalRegistrationForm
from indico.modules.users import User
from indico.util.i18n import _, get_all_locales, parse_locale
from indico.util.string import to_unicode
from indico.web.flask.util import url_for
from indico.web.forms.validators import UsedIfChecked
from indico.web.forms.widgets import SwitchWidget

# TODO: set the time zone  here once communities settings are available.


class RHInitialSetup(RH):

    def _checkProtection(self):
        if User.query.count() > 0:
            raise AccessError

    def _process_GET(self):
        return render_template('initial_setup.html',
                               selected_lang_name=parse_locale(session.lang).language_name,
                               language_options=sorted(get_all_locales().items(), key=itemgetter(1)),
                               form=InitialSetupForm(language=session.lang),
                               timezone=Config.getInstance().getDefaultTimezone())

    def _process_POST(self):
        setup_form = InitialSetupForm(request.form)
        if not setup_form.validate():
            print setup_form.errors
            raise FormValuesError(_("Some fields are invalid. Please, correct them and submit the form again."))

        # Creating new user
        user = User()
        user.first_name = to_unicode(setup_form.first_name.data)
        user.last_name = to_unicode(setup_form.last_name.data)
        user.affiliation = to_unicode(setup_form.affiliation.data)
        user.email = to_unicode(setup_form.email.data)
        user.is_admin = True
        user.settings.set('timezone', Config.getInstance().getDefaultTimezone())
        user.settings.set('lang', to_unicode(setup_form.language.data))

        identity = Identity(provider='indico', identifier=setup_form.username.data, password=setup_form.password.data)
        user.identities.add(identity)
        full_name = user.full_name  # needed after the session closes

        login_user(user, identity)
        db.session.add(user)
        transaction.commit()

        # Configuring server's settings
        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
        minfo.setOrganisation(setup_form.affiliation.data)
        minfo.setLang(setup_form.language.data)
        if setup_form.enable_tracking.data:
            # Posting a request to the server with the data
            services.register_instance(setup_form.it_contact.data, setup_form.it_email.data)

        flash(Markup(
            _("Congrats {name}, Indico is now ready and you are logged in with your new administration account!<br>"
              "Don't forget to tweak <a href=\"{settings_link}\">Indico's settings</a> and update your "
              "<a href=\"{profile_link}\">profile</a>.").format(
                name=full_name, settings_link=url_for('admin.adminList'), profile_link=url_for('users.user_dashboard'))
        ), 'success')

        return redirect(url_for('misc.index'))


class InitialSetupForm(LocalRegistrationForm):
    first_name = TextField('First Name', [validators.Required()])
    last_name = TextField('Last Name', [validators.Required()])
    email = EmailField(_('Email address'), [validators.Required()])
    language = SelectField('Language', [validators.Required()])
    affiliation = TextField('Affiliation', [validators.Required()])
    enable_tracking = BooleanField('Enable Instance Tracking', widget=SwitchWidget())
    contact_name = TextField('Contact Name',
                             [UsedIfChecked('enable_tracking'), validators.Required()])
    contact_email = EmailField('Contact Email Address',
                               [UsedIfChecked('enable_tracking'), validators.Required(), validators.Email()])

    def __init__(self, *args, **kwargs):
        super(InitialSetupForm, self).__init__(*args, **kwargs)
        self.language.choices = sorted(get_all_locales().items(), key=itemgetter(1))

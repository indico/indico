# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from platform import python_version

from flask import flash, redirect, render_template, request, session
from markupsafe import Markup
from requests.exceptions import HTTPError, RequestException, Timeout

import indico
from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import get_postgres_version
from indico.modules.auth import Identity, login_user
from indico.modules.bootstrap.forms import BootstrapForm
from indico.modules.cephalopod.util import register_instance
from indico.modules.core.settings import core_settings
from indico.modules.users import User
from indico.util.i18n import get_all_locales
from indico.util.network import is_private_url
from indico.util.system import get_os
from indico.web.flask.templating import get_template_module
from indico.web.rh import RH
from indico.web.util import url_for_index


class RHBootstrap(RH):
    def _process(self):
        if User.query.filter_by(is_system=False).has_rows():
            return redirect(url_for_index())

        form = BootstrapForm()
        if form.validate_on_submit():
            return self._handle_submit(form)

        return render_template('bootstrap/bootstrap.html',
                               form=form,
                               timezone=config.DEFAULT_TIMEZONE,
                               languages=get_all_locales(),
                               operating_system=get_os(),
                               postgres_version=get_postgres_version(),
                               indico_version=indico.__version__,
                               python_version=python_version(),
                               show_local_warning=(config.DEBUG or is_private_url(request.url_root)))

    def _handle_submit(self, setup_form):
        # Creating new user
        user = User()
        user.first_name = setup_form.first_name.data
        user.last_name = setup_form.last_name.data
        user.affiliation = setup_form.affiliation.data
        user.email = setup_form.email.data
        user.is_admin = True

        identity = Identity(provider='indico', identifier=setup_form.username.data, password=setup_form.password.data)
        user.identities.add(identity)

        db.session.add(user)
        db.session.flush()

        user.settings.set('timezone', config.DEFAULT_TIMEZONE)
        user.settings.set('lang', session.lang or config.DEFAULT_LOCALE)

        login_user(user, identity)
        full_name = user.full_name  # needed after the session closes

        db.session.commit()

        # Configuring server's settings
        core_settings.set('site_organization', setup_form.affiliation.data)

        message = get_template_module('bootstrap/flash_messages.html').bootstrap_success(name=full_name)
        flash(Markup(message), 'success')

        # Activate instance tracking
        if setup_form.enable_tracking.data:
            contact_name = setup_form.contact_name.data
            contact_email = setup_form.contact_email.data

            try:
                register_instance(contact_name, contact_email)
            except (HTTPError, ValueError) as err:
                message = get_template_module('bootstrap/flash_messages.html').community_error(err=str(err))
                category = 'error'
            except Timeout:
                message = get_template_module('bootstrap/flash_messages.html').community_timeout()
                category = 'error'
            except RequestException as exc:
                message = get_template_module('bootstrap/flash_messages.html').community_exception(err=str(exc))
                category = 'error'
            else:
                message = get_template_module('bootstrap/flash_messages.html').community_success()
                category = 'success'
            flash(Markup(message), category)

        return redirect(url_for_index())

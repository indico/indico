# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals

import platform

from flask import flash, jsonify, redirect, request
from requests.exceptions import HTTPError, RequestException, Timeout
from werkzeug.urls import url_join

import indico
from indico.core.config import Config
from indico.core.db.sqlalchemy.util.queries import get_postgres_version
from indico.legacy.webinterface.rh.base import RH
from indico.modules.admin import RHAdminBase
from indico.modules.cephalopod import cephalopod_settings
from indico.modules.cephalopod.forms import CephalopodForm
from indico.modules.cephalopod.util import register_instance, sync_instance, unregister_instance
from indico.modules.cephalopod.views import WPCephalopod
from indico.modules.core.settings import core_settings
from indico.util.i18n import _
from indico.util.system import get_os
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults


class RHCephalopodBase(RHAdminBase):
    pass


class RHCephalopod(RHCephalopodBase):
    def _process_GET(self):
        form = CephalopodForm(request.form, obj=FormDefaults(**cephalopod_settings.get_all()))
        config = Config.getInstance()
        hub_url = url_join(config.getCommunityHubURL(), 'api/instance/{}'.format(cephalopod_settings.get('uuid')))
        cephalopod_settings.set('show_migration_message', False)
        return WPCephalopod.render_template('cephalopod.html', 'cephalopod',
                                            affiliation=core_settings.get('site_organization'),
                                            enabled=cephalopod_settings.get('joined'),
                                            form=form,
                                            indico_version=indico.__version__,
                                            instance_url=config.getBaseURL(),
                                            language=config.getDefaultLocale(),
                                            operating_system=get_os(),
                                            postgres_version=get_postgres_version(),
                                            python_version=platform.python_version(),
                                            hub_url=hub_url)

    def _process_POST(self):
        name = request.form.get('contact_name', cephalopod_settings.get('contact_name'))
        email = request.form.get('contact_email', cephalopod_settings.get('contact_email'))
        enabled = request.form.get('joined', False)
        uuid = cephalopod_settings.get('uuid')
        try:
            if not enabled:
                unregister_instance()
            elif enabled and uuid:
                sync_instance(name, email)
            elif enabled and not uuid:
                register_instance(name, email)
        except HTTPError as err:
            flash(_("Operation failed, the community hub returned: {err.message}").format(err=err), 'error')
        except Timeout:
            flash(_("The operation timed-out. Please try again in a while."), 'error')
        except RequestException as err:
            flash(_("Unexpected exception while contacting the Community Hub: {err.message}").format(err=err))

        return redirect(url_for('.index'))


class RHCephalopodSync(RHCephalopodBase):
    def _process(self):
        if not cephalopod_settings.get('joined'):
            flash(_("Synchronization is not possible if you don't join the community first."),
                  'error')
        else:
            contact_name = cephalopod_settings.get('contact_name')
            contact_email = cephalopod_settings.get('contact_email')
            try:
                sync_instance(contact_name, contact_email)
            except HTTPError as err:
                flash(_("Synchronization failed, the community hub returned: {err.message}").format(err=err),
                      'error')
            except Timeout:
                flash(_("Synchronization timed-out. Please try again in a while."), 'error')
            except RequestException as err:
                flash(_("Unexpected exception while contacting the Community Hub: {err.message}").format(err=err))

            return redirect(url_for('.index'))


class RHSystemInfo(RH):
    def _process(self):
        config = Config.getInstance()
        stats = {'python_version': platform.python_version(),
                 'indico_version': indico.__version__,
                 'operating_system': get_os(),
                 'postgres_version': get_postgres_version(),
                 'language': config.getDefaultLocale(),
                 'debug': config.getDebug()}
        return jsonify(stats)

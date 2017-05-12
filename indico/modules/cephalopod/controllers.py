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

import pkg_resources
import platform
from urlparse import urljoin

from flask import flash, jsonify, redirect, request
from requests.exceptions import HTTPError, RequestException, Timeout

import indico
from indico.core.config import Config
from indico.core.db import db
from indico.modules.admin import RHAdminBase
from indico.modules.cephalopod import cephalopod_settings
from indico.modules.cephalopod.forms import CephalopodForm
from indico.modules.cephalopod.util import register_instance, sync_instance, unregister_instance
from indico.modules.cephalopod.views import WPCephalopod
from indico.modules.core.settings import core_settings
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults

from indico.legacy.webinterface.rh.base import RH


def get_postgres_version():
    version = db.engine.execute("SELECT current_setting('server_version_num')::int").scalar()
    return '{}.{}.{}'.format(version // 10000, version % 10000 // 100, version % 100)


def get_os():
    system_name = platform.system()
    if system_name == 'Linux':
        return '{} {} {}'.format(system_name, platform.linux_distribution()[0], platform.linux_distribution()[1])
    else:
        return '{} {}'.format(system_name, platform.release()).rstrip()


class RHCephalopodBase(RHAdminBase):
    pass


class RHCephalopod(RHCephalopodBase):
    def _process_GET(self):
        defaults = FormDefaults(**cephalopod_settings.get_all())
        form = CephalopodForm(request.form, obj=defaults)

        enabled = cephalopod_settings.get('joined')
        config = Config.getInstance()
        instance_url = config.getBaseURL()
        language = config.getDefaultLocale()
        tracker_url = urljoin(config.getTrackerURL(), 'api/instance/{}'.format(cephalopod_settings.get('uuid')))
        return WPCephalopod.render_template('cephalopod.html', 'cephalopod',
                                            affiliation=core_settings.get('site_organization'),
                                            enabled=enabled,
                                            form=form,
                                            indico_version=indico.__version__,
                                            instance_url=instance_url,
                                            language=language,
                                            operating_system=get_os(),
                                            postgres_version=get_postgres_version(),
                                            python_version=platform.python_version(),
                                            tracker_url=tracker_url)

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
        try:
            indico_version = pkg_resources.get_distribution('indico').version
        except pkg_resources.DistributionNotFound:
            indico_version = 'dev'
        stats = {'python_version': platform.python_version(),
                 'indico_version': indico_version,
                 'operating_system': get_os(),
                 'postgres_version': get_postgres_version(),
                 'language': Config.getInstance().getDefaultLocale()}
        return jsonify(stats)

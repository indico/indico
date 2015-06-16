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

from __future__ import unicode_literals

from platform import python_version
from urlparse import urljoin

from flask import flash, jsonify, redirect, request
from requests.exceptions import HTTPError, Timeout

from indico.core.config import Config
from indico.modules.cephalopod import settings
from indico.modules.cephalopod.forms import CephalopodForm
from indico.modules.cephalopod.util import disable_instance, register_instance, sync_instance
from indico.modules.cephalopod.views import WPCephalopod
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults

import MaKaC
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.webinterface.rh.admins import RHAdminBase
from MaKaC.webinterface.rh.base import RH


class RHCephalopod(RHAdminBase):

    def _process_GET(self):
        defaults = FormDefaults(**settings.get_all())
        form = CephalopodForm(request.form, obj=defaults)

        affiliation = HelperMaKaCInfo.getMaKaCInfoInstance().getOrganisation()
        enabled = settings.get('joined')
        instance_url = Config.getInstance().getBaseURL()
        language = HelperMaKaCInfo.getMaKaCInfoInstance().getLang()
        tracker_url = urljoin(Config.getInstance().getTrackerURL(), 'api/instance/{}'.format(settings.get('uuid')))
        return WPCephalopod.render_template('cephalopod.html',
                                            form=form,
                                            affiliation=affiliation,
                                            indico_version=MaKaC.__version__,
                                            enabled=enabled,
                                            instance_url=instance_url,
                                            language=language,
                                            python_version=python_version(),
                                            tracker_url=tracker_url)

    def _process_POST(self):
        name = request.form.get('contact_name', settings.get('contact_name'))
        email = request.form.get('contact_email', settings.get('contact_email'))
        enabled = request.form.get('joined', False)
        uuid = settings.get('uuid')
        try:
            if not enabled:
                disable_instance()
            elif enabled and uuid:
                sync_instance(name, email)
            elif enabled and not uuid:
                register_instance(name, email)
        except HTTPError as err:
            flash(_("Operation failed, the community hub returned: {err.message}").format(err=err), 'error')
        except Timeout:
            flash(_("The operation timed-out. Please try again in a while."), 'error')

        return redirect(url_for('.index'))


class RHCephalopodSync(RHAdminBase):

    def _process_GET(self):
        if not settings.get('joined'):
            flash(_("Synchronization is not possible if you don't join the community first."),
                  'error')
        else:
            contact_name = settings.get('contact_name')
            contact_email = settings.get('contact_email')
            try:
                sync_instance(contact_name, contact_email)
            except HTTPError as err:
                flash(_("Synchronization failed, the community hub returned: {err.message}").format(err=err),
                      'error')
            except Timeout:
                flash(_("Synchronization timed-out. Please try again in a while."), 'error')

            return redirect(url_for('.index'))


class RHSystemInfo(RH):

    def _process(self):
        language = HelperMaKaCInfo.getMaKaCInfoInstance().getLang()
        stats = {'python_version': python_version(),
                 'indico_version': MaKaC.__version__,
                 'language': language}
        return jsonify(stats)

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

import transaction
from flask import redirect, request, session
from werkzeug.exceptions import NotFound

from indico.core.config import Config
from indico.core.db import db
from indico.modules.events.static.models.static import StaticSite, StaticSiteState
from indico.modules.events.static.tasks import build_static_site
from indico.modules.events.static.views import WPStaticSites
from indico.web.flask.util import send_file, url_for

from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHStaticSiteBase(RHConferenceModifBase):
    pass


class RHStaticSiteList(RHStaticSiteBase):
    def _process(self):
        if not Config.getInstance().getOfflineStore():
            raise NotFound()
        static_sites = StaticSite.find(event_id=self._conf.id).order_by(StaticSite.requested_dt.desc()).all()
        return WPStaticSites.render_template('static_sites.html', self._conf,
                                             event=self._conf, static_sites=static_sites)


class RHStaticSiteBuild(RHStaticSiteBase):
    CSRF_ENABLED = True

    def _process(self):
        static_site = StaticSite(creator=session.user, event=self._conf)
        db.session.add(static_site)
        transaction.commit()
        build_static_site.delay(static_site)
        return redirect(url_for('.list', self._conf))


class RHStaticSiteDownload(RHStaticSiteBase):
    def _process(self):
        static_site = StaticSite.get_one(request.view_args['id'])
        if static_site.state != StaticSiteState.success:
            raise NotFound()
        return send_file('static_site_{0.event_id}.zip'.format(static_site), static_site.path, 'application/zip')

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

from flask import redirect, request, session
from werkzeug.exceptions import NotFound

from indico.core.db import db
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.static.models.static import StaticSite, StaticSiteState
from indico.modules.events.static.tasks import build_static_site
from indico.modules.events.static.views import WPStaticSites
from indico.web.flask.util import url_for


class RHStaticSiteBase(RHManageEventBase):
    pass


class RHStaticSiteList(RHStaticSiteBase):
    def _process(self):
        static_sites = self.event_new.static_sites.order_by(StaticSite.requested_dt.desc()).all()
        return WPStaticSites.render_template('static_sites.html', self._conf,
                                             event=self.event_new, static_sites=static_sites)


class RHStaticSiteBuild(RHStaticSiteBase):
    ALLOW_LOCKED = True

    def _process(self):
        static_site = StaticSite(creator=session.user, event_new=self.event_new)
        db.session.add(static_site)
        db.session.commit()
        build_static_site.delay(static_site)
        return redirect(url_for('.list', self.event_new))


class RHStaticSiteDownload(RHStaticSiteBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.static_site
        }
    }

    def _checkParams(self, params):
        RHStaticSiteBase._checkParams(self, params)
        self.static_site = StaticSite.get_one(request.view_args['id'])

    def _process(self):
        if self.static_site.state != StaticSiteState.success:
            raise NotFound
        return self.static_site.send()

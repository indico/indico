# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

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
        static_sites = self.event.static_sites.order_by(StaticSite.requested_dt.desc()).all()
        return WPStaticSites.render_template('static_sites.html', self.event, static_sites=static_sites)


class RHStaticSiteBuild(RHStaticSiteBase):
    ALLOW_LOCKED = True

    def _process(self):
        static_site = StaticSite(creator=session.user, event=self.event)
        db.session.add(static_site)
        db.session.commit()
        build_static_site.delay(static_site)
        return redirect(url_for('.list', self.event))


class RHStaticSiteDownload(RHStaticSiteBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.static_site
        }
    }

    def _process_args(self):
        RHStaticSiteBase._process_args(self)
        self.static_site = StaticSite.get_or_404(request.view_args['id'])

    def _process(self):
        if self.static_site.state != StaticSiteState.success:
            raise NotFound
        return self.static_site.send()

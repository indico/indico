# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from datetime import timedelta

from celery.schedules import crontab
from flask import session, g

from indico.core.celery import celery
from indico.core.db import db
from indico.core.notifications import make_email, email_sender
from indico.modules.events.static import logger
from indico.modules.events.static.models.static import StaticSite, StaticSiteState
from indico.util.contextManager import ContextManager
from indico.util.date_time import now_utc
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for

from MaKaC.accessControl import AccessWrapper
from MaKaC.common.offlineWebsiteCreator import OfflineEvent
from MaKaC.webinterface.rh.conferenceBase import RHCustomizable


@celery.task(request_context=True)
def build_static_site(static_site):
    static_site.state = StaticSiteState.running
    db.session.commit()
    try:
        logger.info('Building static site: {}'.format(static_site))
        session.lang = static_site.creator.settings.get('lang')
        rh = RHCustomizable()
        rh._aw = AccessWrapper()
        rh._conf = rh._target = static_site.event

        g.rh = rh
        ContextManager.set('currentRH', rh)
        ContextManager.set('offlineMode', True)

        # Get event type
        wf = rh.getWebFactory()
        event_type = wf.getId() if wf else 'conference'

        zip_file_path = OfflineEvent(rh, rh._conf, event_type).create(static_site.id)

        static_site.path = zip_file_path
        static_site.state = StaticSiteState.success
        db.session.commit()

        logger.info('Building static site successful: {}'.format(static_site))
        ContextManager.set('offlineMode', False)
        ContextManager.set('currentRH', None)
        notify_static_site_success(static_site)
    except Exception:
        logger.exception('Building static site failed: {}'.format(static_site))
        static_site.state = StaticSiteState.failed
        db.session.commit()
        raise
    finally:
        ContextManager.set('offlineMode', False)
        ContextManager.set('currentRH', None)


@email_sender
def notify_static_site_success(static_site):
    template = get_template_module('events/static/emails/download_notification_email.txt',
                                   user=static_site.creator, event=static_site.event,
                                   link=url_for('static_site.download', static_site, _external=True))
    return make_email({static_site.creator.email}, template=template, html=False)


@celery.periodic_task(name='static_sites_cleanup', run_every=crontab(minute='30', hour='3', day_of_week='monday'))
def static_sites_cleanup(days=30):
    """Clean up old static sites

    :param days: number of days after which to remove static sites
    """
    expired_sites = StaticSite.find_all(StaticSite.requested_dt < (now_utc() - timedelta(days=days)),
                                        StaticSite.state == StaticSiteState.success)
    logger.info('Removing {0} expired static sites from the past {1} days'.format(len(expired_sites), days))
    try:
        for site in expired_sites:
            site.delete_file()
            site.path = None
            site.state = StaticSiteState.expired
            logger.info('Removed static site {}'.format(site))
    finally:
        db.session.commit()

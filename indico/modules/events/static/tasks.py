# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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
from flask import g, session

from indico.core.celery import celery
from indico.core.db import db
from indico.core.notifications import email_sender, make_email
from indico.core.storage import StorageReadOnlyError
from indico.legacy.common.offlineWebsiteCreator import create_static_site
from indico.modules.events.static import logger
from indico.modules.events.static.models.static import StaticSite, StaticSiteState
from indico.util.date_time import now_utc
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.rh import RH


@celery.task(request_context=True)
def build_static_site(static_site):
    static_site.state = StaticSiteState.running
    db.session.commit()
    try:
        logger.info('Building static site: %s', static_site)
        session.lang = static_site.creator.settings.get('lang')
        rh = RH()
        g.rh = rh
        g.static_site = True

        zip_file_path = create_static_site(rh, static_site.event)
        static_site.state = StaticSiteState.success
        static_site.content_type = 'application/zip'
        static_site.filename = 'offline_site_{}.zip'.format(static_site.event.id)
        with open(zip_file_path, 'rb') as f:
            static_site.save(f)
        db.session.commit()

        logger.info('Building static site successful: %s', static_site)
        g.static_site = False
        g.rh = None
        notify_static_site_success(static_site)
    except Exception:
        logger.exception('Building static site failed: %s', static_site)
        static_site.state = StaticSiteState.failed
        db.session.commit()
        raise
    finally:
        g.static_site = False
        g.rh = None


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
    logger.info('Removing %d expired static sites from the past %d days', len(expired_sites), days)
    try:
        for site in expired_sites:
            try:
                site.delete()
            except StorageReadOnlyError:
                # If a site is on read-only storage we simply keep it alive.
                logger.debug('Could not delete static site %r (read-only storage)', site)
            else:
                site.state = StaticSiteState.expired
                logger.info('Removed static site %r', site)
    finally:
        db.session.commit()

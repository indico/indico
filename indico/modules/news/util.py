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

from indico.core.db import db
from indico.modules.news import news_settings
from indico.modules.news.models.news import NewsItem
from indico.util.caching import memoize_redis
from indico.util.date_time import now_utc


@memoize_redis(3600)
def get_recent_news():
    """Get a list of recent news for the home page"""
    settings = news_settings.get_all()
    if not settings['show_recent']:
        return []
    delta = timedelta(days=settings['max_age']) if settings['max_age'] else None
    return (NewsItem.query
            .filter(db.cast(NewsItem.created_dt, db.Date) > (now_utc() - delta).date() if delta else True)
            .order_by(NewsItem.created_dt.desc())
            .limit(settings['max_entries'])
            .all())

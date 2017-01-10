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

import re
from HTMLParser import HTMLParser
from operator import attrgetter

from indico.core.db import db
from indico.modules.news import news_settings
from indico.modules.news.models.news import NewsItem
from indico.web.flask.templating import strip_tags

from indico_zodbimport import Importer, convert_to_unicode


class NewsImporter(Importer):
    def has_data(self):
        return NewsItem.query.has_rows()

    def migrate(self):
        self.migrate_settings()
        self.migrate_news()

    def migrate_settings(self):
        self.print_step('migrating news settings')
        mod = self.zodb_root['modules']['news']
        minfo = self.zodb_root['MaKaCInfo']['main']
        news_settings.set('show_recent', bool(minfo._newsActive))
        news_settings.set('new_days', int(mod._recentDays))
        db.session.commit()

    def _sanitize_title(self, title, _ws_re=re.compile(r'\s+')):
        title = convert_to_unicode(title)
        title = HTMLParser().unescape(strip_tags(title))
        return _ws_re.sub(' ', title).strip()

    def migrate_news(self):
        self.print_step('migrating news')
        old_items = sorted(self.zodb_root['modules']['news']._newsItems, key=attrgetter('_creationDate'))
        for old_item in old_items:
            n = NewsItem(title=self._sanitize_title(old_item._title), content=convert_to_unicode(old_item._content),
                         created_dt=old_item._creationDate)
            db.session.add(n)
            db.session.flush()
            self.print_success(n.title)
        db.session.commit()

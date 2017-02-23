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

from datetime import timedelta

from flask import flash, request, redirect, session

from indico.core.db import db
from indico.modules.admin import RHAdminBase
from indico.modules.news import news_settings, logger
from indico.modules.news.forms import NewsSettingsForm, NewsForm
from indico.modules.news.models.news import NewsItem
from indico.modules.news.util import get_recent_news
from indico.modules.news.views import WPNews, WPManageNews
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form
from MaKaC.webinterface.rh.base import RH


class RHNews(RH):
    CSRF_ENABLED = True

    @staticmethod
    def _is_new(item):
        days = news_settings.get('new_days')
        if not days:
            return False
        return item.created_dt.date() >= (now_utc() - timedelta(days=days)).date()

    def _process(self):
        news = NewsItem.query.order_by(NewsItem.created_dt.desc()).all()
        return WPNews.render_template('news.html', news=news, _is_new=self._is_new)


class RHManageNewsBase(RHAdminBase):
    pass


class RHManageNews(RHManageNewsBase):
    def _process(self):
        news = NewsItem.query.order_by(NewsItem.created_dt.desc()).all()
        return WPManageNews.render_template('admin/news.html', news=news)


class RHNewsSettings(RHManageNewsBase):
    def _process(self):
        form = NewsSettingsForm(obj=FormDefaults(**news_settings.get_all()))
        if form.validate_on_submit():
            news_settings.set_multi(form.data)
            get_recent_news.clear_cached()
            flash(_('Settings have been saved'), 'success')
            return jsonify_data()
        return jsonify_form(form)


class RHCreateNews(RHManageNewsBase):
    def _process(self):
        form = NewsForm()
        if form.validate_on_submit():
            item = NewsItem()
            form.populate_obj(item)
            db.session.add(item)
            db.session.flush()
            get_recent_news.clear_cached()
            logger.info('News %r created by %s', item, session.user)
            flash(_("News '{title}' has been posted").format(title=item.title), 'success')
            return jsonify_data(flash=False)
        return jsonify_form(form)


class RHManageNewsItemBase(RHManageNewsBase):
    def _checkParams(self, params):
        RHManageNewsBase._checkParams(self, params)
        self.item = NewsItem.get_one(request.view_args['news_id'])


class RHEditNews(RHManageNewsItemBase):
    def _process(self):
        form = NewsForm(obj=self.item)
        if form.validate_on_submit():
            old_title = self.item.title
            form.populate_obj(self.item)
            db.session.flush()
            get_recent_news.clear_cached()
            logger.info('News %r modified by %s', self.item, session.user)
            flash(_("News '{title}' has been updated").format(title=old_title), 'success')
            return jsonify_data(flash=False)
        return jsonify_form(form)


class RHDeleteNews(RHManageNewsItemBase):
    def _process(self):
        db.session.delete(self.item)
        get_recent_news.clear_cached()
        flash(_("News '{title}' has been deleted").format(title=self.item.title), 'success')
        logger.info('News %r deleted by %r', self.item, session.user)
        return redirect(url_for('news.manage'))

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

from indico.modules.news.controllers import RHCreateNews, RHDeleteNews, RHEditNews, RHManageNews, RHNews, RHNewsSettings
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('news', __name__, template_folder='templates', virtual_template_folder='news')

_bp.add_url_rule('/news', 'display', RHNews)
_bp.add_url_rule('/admin/news/', 'manage', RHManageNews)
_bp.add_url_rule('/admin/news/settings', 'settings', RHNewsSettings, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/news/create', 'create_news', RHCreateNews, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/news/<int:news_id>/', 'edit_news', RHEditNews, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/news/<int:news_id>/delete', 'delete_news', RHDeleteNews, methods=('GET', 'POST'))

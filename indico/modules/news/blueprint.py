# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.news.controllers import (RHCreateNews, RHDeleteNews, RHEditNews, RHManageNews, RHNews, RHNewsItem,
                                             RHNewsSettings)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('news', __name__, template_folder='templates', virtual_template_folder='news')

_bp.add_url_rule('/news/', 'display', RHNews)
_bp.add_url_rule('/news/<int:news_id>', 'display_item', RHNewsItem)
_bp.add_url_rule('/news/<int:news_id>-<slug>', 'display_item', RHNewsItem)
_bp.add_url_rule('/admin/news/', 'manage', RHManageNews)
_bp.add_url_rule('/admin/news/settings', 'settings', RHNewsSettings, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/news/create', 'create_news', RHCreateNews, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/news/<int:news_id>/', 'edit_news', RHEditNews, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/news/<int:news_id>/delete', 'delete_news', RHDeleteNews, methods=('GET', 'POST'))

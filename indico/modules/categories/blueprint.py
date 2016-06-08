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

from indico.modules.categories.controllers import (RHCategoryStatistics, RHCategoryMoveContents,
                                                   RHCategoryInfo)
from indico.web.flask.wrappers import IndicoBlueprint

_bp = IndicoBlueprint('categories', __name__, template_folder='templates', url_prefix='/category')

_bp.add_url_rule('/<categId>/statistics', 'category-statistics', RHCategoryStatistics)
_bp.add_url_rule('/<categId>/manage/move/', 'move-contents', RHCategoryMoveContents)
# TODO: Change to <int:category_id>
_bp.add_url_rule('/<categId>/info', 'info', RHCategoryInfo)

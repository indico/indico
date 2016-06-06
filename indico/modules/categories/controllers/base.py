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

from flask import request, session
from werkzeug.exceptions import NotFound, Forbidden

from indico.modules.categories.models.categories import Category
from indico.util.i18n import _
from indico.web.flask.util import url_for

from MaKaC.webinterface.rh.base import RH, RHDisplayBaseProtected, RHModificationBaseProtected


class RHCategoryBase(RH):
    def _checkParams(self, params):
        category_id = request.view_args['category_id']
        self.category = Category.get(category_id)
        if self.category is None:
            raise NotFound(_("The category with id '{}' does not exist or has been deleted").format(
                           category_id),
                           title=_("Category not found"))


class RHDisplayCategoryBase(RHCategoryBase):
    def _checkProtection(self):
        if not self.category.can_access(session.user):
            raise Forbidden


class RHManageCategoryBase(RHCategoryBase):
    def _checkProtection(self):
        if not self.category.can_manage(session.user):
            raise Forbidden

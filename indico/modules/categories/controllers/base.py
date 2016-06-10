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

from flask import request, session
from werkzeug.exceptions import NotFound, Forbidden

from indico.modules.categories.models.categories import Category
from indico.util.i18n import _
from MaKaC.webinterface.rh.base import RH


class RHCategoryBase(RH):
    CSRF_ENABLED = True

    def _checkParams(self):
        category_id = request.view_args['category_id']
        self.category = Category.get(category_id, is_deleted=False)
        if self.category is None:
            raise NotFound(_("This category does not exist or has been deleted."))


class RHDisplayCategoryBase(RHCategoryBase):
    def _checkProtection(self):
        if not self.category.can_access(session.user):
            msg = [_("You are not authorized to access this category.")]
            if self.category.no_access_contact:
                msg.append(_("If you believe you should have access, please contact {}")
                           .format(self.category.no_access_contact))
            raise Forbidden(' '.join(msg))


class RHManageCategoryBase(RHCategoryBase):
    def _checkProtection(self):
        if not self.category.can_manage(session.user):
            raise Forbidden

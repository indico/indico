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

from flask import flash, request

from indico.core.db import db
from indico.modules.admin import RHAdminBase
from indico.modules.events.forms import ReferenceTypeForm
from indico.modules.events.models.references import ReferenceType
from indico.modules.events.operations import create_reference_type, delete_reference_type, update_reference_type
from indico.modules.events.views import WPReferenceTypes
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form


def _get_all_reference_types():
    return ReferenceType.query.order_by(db.func.lower(ReferenceType.name)).all()


def _render_reference_type_list():
    tpl = get_template_module('events/admin/_reference_type_list.html')
    return tpl.render_reference_type_list(_get_all_reference_types())


class RHManageReferenceTypeBase(RHAdminBase):
    """Base class for a specific reference type"""

    def _process_args(self):
        RHAdminBase._process_args(self)
        self.reference_type = ReferenceType.find_one(id=request.view_args['reference_type_id'])


class RHReferenceTypes(RHAdminBase):
    """Manage reference types in server admin area"""

    def _process(self):
        types = _get_all_reference_types()
        return WPReferenceTypes.render_template('admin/reference_types.html', 'reference_types', reference_types=types)


class RHCreateReferenceType(RHAdminBase):
    """Create a new reference type"""

    def _process(self):
        form = ReferenceTypeForm()
        if form.validate_on_submit():
            reference_type = create_reference_type(form.data)
            flash(_("External ID type '{}' created successfully").format(reference_type.name), 'success')
            return jsonify_data(html=_render_reference_type_list())
        return jsonify_form(form)


class RHEditReferenceType(RHManageReferenceTypeBase):
    """Edit an existing reference type"""

    def _process(self):
        form = ReferenceTypeForm(obj=FormDefaults(self.reference_type), reference_type=self.reference_type)
        if form.validate_on_submit():
            update_reference_type(self.reference_type, form.data)
            flash(_("External ID type '{}' successfully updated").format(self.reference_type.name), 'success')
            return jsonify_data(html=_render_reference_type_list())
        return jsonify_form(form)


class RHDeleteReferenceType(RHManageReferenceTypeBase):
    """Delete an existing reference type"""

    def _process_DELETE(self):
        delete_reference_type(self.reference_type)
        flash(_("External ID type '{}' successfully deleted").format(self.reference_type.name), 'success')
        return jsonify_data(html=_render_reference_type_list())

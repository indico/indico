# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from flask import request, jsonify, session

from indico.core.db import db
from indico.modules.events.registration import logger
from indico.modules.events.registration.controllers.management.sections import RHManageRegFormSectionBase
from indico.modules.events.registration.models.registration_form_fields import RegistrationFormField
from indico.web.util import jsonify_data


class RHManageRegFormFieldBase(RHManageRegFormSectionBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.field
        }
    }

    def _checkParams(self, params):
        RHManageRegFormSectionBase._checkParams(self, params)
        self.field = RegistrationFormField.get_one(request.view_args['field_id'])


class RHToggleFieldState(RHManageRegFormFieldBase):
    def _process(self):
        self.field.is_enabled = (request.args.get('enable') == 'true')
        db.session.flush()
        logger.info('Field {} modified by {}'.format(self.field, session.user))
        return jsonify_data(**self.field.view_data)


class RHDeleteRegFormField(RHManageRegFormFieldBase):
    def _process(self):
        self.field.is_deleted = True
        db.session.flush()
        logger.info('Field {} deleted by {}'.format(self.field, session.user))
        return jsonify_data(success=True)


class RHMoveField(RHManageRegFormFieldBase):
    def _process(self):
        new_position = request.json['endPos'] + 1
        old_position = self.field.position
        if new_position == old_position:
            return jsonify(success=True)
        elif new_position < old_position:
            def fn(field):
                return field.position >= new_position and field.id != self.field.id and not field.is_deleted
            start_enum = new_position + 1
        else:
            def fn(field):
                return (field.position > old_position and field.position <= new_position
                        and field.id != self.field.id and not field.is_deleted)
            start_enum = self.field.position
        to_update = filter(fn, self.section.children)
        self.field.position = new_position
        for pos, field in enumerate(to_update, start_enum):
            field.position = pos
        db.session.flush()
        return jsonify(success=True)

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
from indico.modules.events.registration.controllers.management import RHManageRegFormBase
from indico.modules.events.registration.models.items import RegistrationFormSection
from indico.modules.events.registration.models.registration_form_fields import (RegistrationFormField,
                                                                                RegistrationFormFieldData)
from indico.web.util import jsonify_data


class RHManageRegFormSectionBase(RHManageRegFormBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.section
        }
    }

    def _checkParams(self, params):
        RHManageRegFormBase._checkParams(self, params)
        self.section = RegistrationFormSection.get_one(request.view_args['section_id'])


class RHRegFormAddSection(RHManageRegFormBase):
    def _process(self):
        section = RegistrationFormSection(registration_form=self.regform)
        section.title = request.json['title']
        section.description = request.json.get('description')
        db.session.add(section)
        db.session.flush()
        logger.info('Section {} created by {}'.format(section, session.user))
        return jsonify_data(**section.view_data)


class RHRegFormModifySection(RHManageRegFormSectionBase):
    def _process_POST(self):
        self.section.is_enabled = (request.args.get('enable') == 'true')
        db.session.flush()
        logger.info('Section {} modified by {}'.format(self.section, session.user))
        return jsonify_data(**self.section.view_data)

    def _process_DELETE(self):
        self.section.is_deleted = True
        db.session.flush()
        logger.info('Section {} deleted by {}'.format(self.section, session.user))
        return jsonify(success=True)

    def _process_PATCH(self):
        modified_field = request.args.get('modified')
        if modified_field in {'title', 'description'}:
            setattr(self.section, modified_field, request.json.get(modified_field))
        db.session.flush()
        logger.info('Section {} modified by {}'.format(self.section, session.user))
        return jsonify(self.section.view_data)


class RHRegFormAddField(RHManageRegFormSectionBase):
    def _process(self):
        field_data = request.json['fieldData']
        form_field = RegistrationFormField(parent_id=self.section.id,
                                           registration_form=self.regform)
        form_field.data.append(RegistrationFormFieldData(data=field_data))
        form_field.title = field_data.pop('caption')
        form_field.description = field_data.pop('description', '')
        form_field.is_enabled = not field_data.pop('disabled')
        db.session.add(form_field)
        db.session.flush()
        return jsonify(form_field.view_data)


class RHRegFormMoveSection(RHManageRegFormSectionBase):
    def _process(self):
        new_position = request.json['endPos'] + 1
        old_position = self.section.position
        if new_position == old_position:
            return jsonify(success=True)
        elif new_position < old_position:
            def fn(section):
                return section.position >= new_position and section.id != self.section.id
            start_enum = new_position + 1
        else:
            def fn(section):
                return (section.position > old_position and section.position <= new_position
                        and section.id != self.section.id)
            start_enum = self.section.position
        to_update = filter(fn, RegistrationFormSection.find(registration_form=self.regform, is_deleted=False)
                                                      .order_by(RegistrationFormSection.position).all())
        self.section.position = new_position
        for pos, section in enumerate(to_update, start_enum):
            section.position = pos
        db.session.flush()
        return jsonify(success=True)

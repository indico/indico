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

from flask import jsonify, request, session
from werkzeug.exceptions import BadRequest

from indico.core.db import db
from indico.modules.events.registration import logger
from indico.modules.events.registration.controllers.management import RHManageRegFormBase
from indico.modules.events.registration.models.items import RegistrationFormItemType, RegistrationFormSection
from indico.modules.events.registration.util import update_regform_item_positions
from indico.web.util import jsonify_data


class RHManageRegFormSectionBase(RHManageRegFormBase):
    """Base class for a specific registration form section"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.section
        }
    }

    def _process_args(self):
        RHManageRegFormBase._process_args(self)
        self.section = RegistrationFormSection.get_one(request.view_args['section_id'])


class RHRegistrationFormAddSection(RHManageRegFormBase):
    """Add a section to the registration form"""

    def _process(self):
        section = RegistrationFormSection(registration_form=self.regform)
        section.title = request.json['title']
        section.description = request.json.get('description')
        section.is_manager_only = request.json['is_manager_only']
        db.session.add(section)
        db.session.flush()
        logger.info('Section %s created by %s', section, session.user)
        return jsonify_data(**section.view_data)


class RHRegistrationFormModifySection(RHManageRegFormSectionBase):
    """Delete/modify a section"""

    def _process_DELETE(self):
        if self.section.type == RegistrationFormItemType.section_pd:
            raise BadRequest
        self.section.is_deleted = True
        db.session.flush()
        logger.info('Section %s deleted by %s', self.section, session.user)
        return jsonify(success=True)

    def _process_PATCH(self):
        changes = request.json['changes']
        if set(changes.viewkeys()) > {'title', 'description'}:
            raise BadRequest
        for field, value in changes.iteritems():
            setattr(self.section, field, value)
        db.session.flush()
        logger.info('Section %s modified by %s: %s', self.section, session.user, changes)
        return jsonify(self.section.view_data)


class RHRegistrationFormToggleSection(RHManageRegFormSectionBase):
    """Enable/disable a section"""

    def _process_POST(self):
        enabled = request.args.get('enable') == 'true'
        if not enabled and self.section.type == RegistrationFormItemType.section_pd:
            raise BadRequest
        self.section.is_enabled = enabled
        update_regform_item_positions(self.regform)
        db.session.flush()
        if self.section.is_enabled:
            logger.info('Section %s enabled by %s', self.section, session.user)
        else:
            logger.info('Section %s disabled by %s', self.section, session.user)
        return jsonify_data(**self.section.view_data)


class RHRegistrationFormMoveSection(RHManageRegFormSectionBase):
    """Move a section within the registration form"""

    def _process(self):
        new_position = request.json['endPos'] + 1
        old_position = self.section.position
        if new_position == old_position:
            return jsonify(success=True)
        elif new_position < old_position:
            def fn(section):
                return (section.position >= new_position and section.id != self.section.id and not section.is_deleted
                        and section.is_enabled)
            start_enum = new_position + 1
        else:
            def fn(section):
                return (old_position < section.position <= new_position and section.id != self.section.id
                        and not section.is_deleted and section.is_enabled)
            start_enum = self.section.position
        to_update = filter(fn, RegistrationFormSection.find(registration_form=self.regform, is_deleted=False)
                                                      .order_by(RegistrationFormSection.position).all())
        self.section.position = new_position
        for pos, section in enumerate(to_update, start_enum):
            section.position = pos
        db.session.flush()
        return jsonify(success=True)

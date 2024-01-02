# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify, request, session
from werkzeug.exceptions import BadRequest

from indico.core.db import db
from indico.modules.events.registration import logger
from indico.modules.events.registration.controllers.management import RHManageRegFormBase
from indico.modules.events.registration.models.items import RegistrationFormItemType, RegistrationFormSection
from indico.modules.events.registration.util import get_flat_section_positions_setup_data, update_regform_item_positions
from indico.modules.logs.models.entries import EventLogRealm, LogKind
from indico.modules.logs.util import make_diff_log
from indico.web.util import jsonify_data


class RHManageRegFormSectionBase(RHManageRegFormBase):
    """Base class for a specific registration form section."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.section
        }
    }

    def _process_args(self):
        RHManageRegFormBase._process_args(self)
        self.section = RegistrationFormSection.get_or_404(request.view_args['section_id'])


class RHRegistrationFormAddSection(RHManageRegFormBase):
    """Add a section to the registration form."""

    def _process(self):
        section = RegistrationFormSection(registration_form=self.regform)
        section.title = request.json['title']
        section.description = request.json.get('description')
        section.is_manager_only = request.json.get('is_manager_only', False)
        db.session.add(section)
        db.session.flush()
        section.log(
            EventLogRealm.management, LogKind.positive, 'Registration',
            f'Section "{section.title}" in "{self.regform.title}" added', session.user,
            data={'Manager-only': section.is_manager_only}
        )
        logger.info('Section %s created by %s', section, session.user)
        return jsonify(section.view_data)


class RHRegistrationFormModifySection(RHManageRegFormSectionBase):
    """Delete/modify a section."""

    def _process_DELETE(self):
        if self.section.type == RegistrationFormItemType.section_pd:
            raise BadRequest
        self.section.is_deleted = True
        db.session.flush()
        self.section.log(
            EventLogRealm.management, LogKind.negative, 'Registration',
            f'Section "{self.section.title}" in "{self.regform.title}" deleted', session.user
        )
        logger.info('Section %s deleted by %s', self.section, session.user)
        return jsonify(success=True)

    def _process_PATCH(self):
        changes = request.json['changes']
        if set(changes.keys()) > {'title', 'description', 'is_manager_only'}:
            raise BadRequest
        if self.section.type == RegistrationFormItemType.section_pd and changes.get('is_manager_only'):
            raise BadRequest
        changes = self.section.populate_from_dict(changes)
        db.session.flush()
        changes = make_diff_log(changes, {
            'title': {'title': 'Title', 'type': 'string'},
            'description': {'title': 'Description'},
            'is_manager_only': {'title': 'Manager-only'},
        })
        self.section.log(
            EventLogRealm.management, LogKind.change, 'Registration',
            f'Section "{self.section.title}" in "{self.regform.title}" modified', session.user,
            data={'Changes': changes}
        )
        logger.info('Section %s modified by %s: %s', self.section, session.user, changes)
        return jsonify(self.section.view_data)


class RHRegistrationFormToggleSection(RHManageRegFormSectionBase):
    """Enable/disable a section."""

    def _process_POST(self):
        enabled = request.args.get('enable') == 'true'
        if not enabled and self.section.type == RegistrationFormItemType.section_pd:
            raise BadRequest
        self.section.is_enabled = enabled
        update_regform_item_positions(self.regform)
        db.session.flush()
        if self.section.is_enabled:
            self.section.log(
                EventLogRealm.management, LogKind.positive, 'Registration',
                f'Section "{self.section.title}" in "{self.regform.title}" enabled', session.user
            )
            logger.info('Section %s enabled by %s', self.section, session.user)
        else:
            self.section.log(
                EventLogRealm.management, LogKind.negative, 'Registration',
                f'Section "{self.section.title}" in "{self.regform.title}" disabled', session.user
            )
            logger.info('Section %s disabled by %s', self.section, session.user)
        return jsonify_data(view_data=self.section.view_data,
                            positions=get_flat_section_positions_setup_data(self.regform))


class RHRegistrationFormMoveSection(RHManageRegFormSectionBase):
    """Move a section within the registration form."""

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
        to_update = list(filter(fn,
                                RegistrationFormSection.query
                                .filter_by(registration_form=self.regform, is_deleted=False)
                                .order_by(RegistrationFormSection.position)
                                .all()))
        self.section.position = new_position
        for pos, section in enumerate(to_update, start_enum):
            section.position = pos
        db.session.flush()
        return jsonify(success=True)

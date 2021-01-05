# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import flash, request, session

from indico.core.db import db
from indico.modules.events import EventLogKind, EventLogRealm
from indico.modules.events.contributions import Contribution
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.logs.util import make_diff_log
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.management.forms import ProgramCodesForm
from indico.modules.events.management.program_codes import generate_program_codes
from indico.modules.events.management.settings import program_codes_settings
from indico.modules.events.management.views import WPEventProgramCodes
from indico.modules.events.sessions import Session
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.timetable import TimetableEntry
from indico.util.i18n import _
from indico.util.placeholders import render_placeholder_info
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


class RHProgramCodes(RHManageEventBase):
    def _process(self):
        templates = program_codes_settings.get_all(self.event)
        return WPEventProgramCodes.render_template('program_codes.html', self.event, 'program_codes',
                                                   templates=templates)


class RHProgramCodeTemplates(RHManageEventBase):
    def _process(self):
        form = ProgramCodesForm(obj=FormDefaults(**program_codes_settings.get_all(self.event)))
        contribution_placeholders = render_placeholder_info('program-codes-contribution', contribution=None)
        subcontribution_placeholders = render_placeholder_info('program-codes-subcontribution', subcontribution=None)
        session_placeholders = render_placeholder_info('program-codes-session', session=None)
        session_block_placeholders = render_placeholder_info('program-codes-session-block', session_block=None)
        form.contribution_template.description = contribution_placeholders
        form.subcontribution_template.description = subcontribution_placeholders
        form.session_template.description = session_placeholders
        form.session_block_template.description = session_block_placeholders

        if form.validate_on_submit():
            program_codes_settings.set_multi(self.event, form.data)
            return jsonify_data(flash=False)

        return jsonify_form(form)


class RHAssignProgramCodesBase(RHManageEventBase):
    object_type = None
    show_dates = True
    hidden_post_field = None

    def _process_args(self):
        RHManageEventBase._process_args(self)
        self.objects = self._get_objects()

    def _get_objects(self):
        raise NotImplementedError

    def _get_update_log_data(self, updates):
        changes = {}
        fields = {}
        for obj, change in updates.viewitems():
            title = getattr(obj, 'full_title', obj.title)
            friendly_id = getattr(obj, 'friendly_id', None)
            if friendly_id is not None:
                title = '#{}: {}'.format(friendly_id, title)
            key = 'obj_{}'.format(obj.id)
            fields[key] = {'type': 'string', 'title': title}
            changes[key] = change
        return {'Changes': make_diff_log(changes, fields)}

    def _process(self):
        if 'assign' in request.form:
            updates = {}
            for obj in self.objects:
                code = request.form['code_{}'.format(obj.id)].strip()
                if code != obj.code:
                    updates[obj] = (obj.code, code)
                    obj.code = code
            if updates:
                flash(_('The programme codes have been successfully assigned'), 'success')
                self.event.log(EventLogRealm.management, EventLogKind.change, 'Programme',
                               'Programme codes assigned to {}'.format(self.object_type.replace('-', ' ')),
                               session.user, data=self._get_update_log_data(updates))
            else:
                flash(_('No codes have been changed'), 'info')
            return jsonify_data()
        codes = generate_program_codes(self.event, self.object_type, self.objects)
        return jsonify_template('events/management/assign_program_codes.html', event=self.event, codes=codes,
                                show_dates=self.show_dates, hidden_post_field=self.hidden_post_field,
                                object_type=self.object_type)


class RHAssignProgramCodesSessions(RHAssignProgramCodesBase):
    object_type = 'sessions'
    show_dates = False
    hidden_post_field = 'session_id'

    def _get_objects(self):
        ids = map(int, request.form.getlist('session_id'))
        return (Session.query
                .with_parent(self.event)
                .filter(Session.id.in_(ids) if ids else True)
                .order_by(db.func.lower(Session.title))
                .all())


class RHAssignProgramCodesSessionBlocks(RHAssignProgramCodesBase):
    object_type = 'session-blocks'

    def _get_objects(self):
        return (SessionBlock.query
                .filter(SessionBlock.session.has(event=self.event, is_deleted=False))
                .join(Session)
                .join(TimetableEntry)
                .order_by(TimetableEntry.start_dt,
                          db.func.lower(Session.title),
                          db.func.lower(SessionBlock.title),
                          SessionBlock.id)
                .all())


class RHAssignProgramCodesContributions(RHAssignProgramCodesBase):
    object_type = 'contributions'
    hidden_post_field = 'contribution_id'

    def _get_objects(self):
        ids = map(int, request.form.getlist('contribution_id'))
        return (Contribution.query
                .with_parent(self.event)
                .filter(Contribution.id.in_(ids) if ids else True)
                .outerjoin(TimetableEntry)
                .order_by(TimetableEntry.start_dt,
                          db.func.lower(Contribution.title),
                          Contribution.friendly_id)
                .all())


class RHAssignProgramCodesSubContributions(RHAssignProgramCodesBase):
    object_type = 'subcontributions'
    show_dates = False

    def _get_objects(self):
        return (SubContribution.query
                .filter(~SubContribution.is_deleted,
                        SubContribution.contribution.has(event=self.event, is_deleted=False))
                .join(Contribution)
                .outerjoin(TimetableEntry)
                .order_by(TimetableEntry.start_dt,
                          db.func.lower(Contribution.title),
                          SubContribution.position)
                .all())

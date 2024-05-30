# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import flash, jsonify, request, session
from webargs import fields
from webargs.flaskparser import abort

from indico.core.db import db
from indico.modules.events import EventLogRealm
from indico.modules.events.contributions import Contribution
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.management.forms import ProgramCodesForm
from indico.modules.events.management.program_codes import generate_program_codes
from indico.modules.events.management.settings import program_codes_settings
from indico.modules.events.management.views import WPEventProgramCodes
from indico.modules.events.sessions import Session
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.timetable import TimetableEntry
from indico.modules.logs import LogKind
from indico.modules.logs.util import make_diff_log
from indico.util.i18n import _
from indico.util.placeholders import render_placeholder_info
from indico.web.args import use_kwargs
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


def _get_update_log_data(updates):
    changes = {}
    fields = {}
    for obj, change in updates.items():
        title = getattr(obj, 'full_title', obj.title)
        friendly_id = getattr(obj, 'friendly_id', None)
        if friendly_id is not None:
            title = f'#{friendly_id}: {title}'
        key = f'obj_{obj.id}'
        fields[key] = {'type': 'string', 'title': title}
        changes[key] = change
    return {'Changes': make_diff_log(changes, fields)}


class RHAssignProgramCodesBase(RHManageEventBase):
    object_type = None
    show_dates = True
    hidden_post_field = None

    def _process_args(self):
        RHManageEventBase._process_args(self)
        self.objects = self._get_objects()

    def _get_objects(self):
        raise NotImplementedError

    def _process(self):
        if 'assign' in request.form:
            updates = {}
            for obj in self.objects:
                code = request.form[f'code_{obj.id}'].strip()
                if code != obj.code:
                    updates[obj] = (obj.code, code)
                    obj.code = code
            if updates:
                flash(_('The program codes have been successfully assigned'), 'success')
                self.event.log(EventLogRealm.management, LogKind.change, 'Program',
                               'Program codes assigned to {}'.format(self.object_type.replace('-', ' ')),
                               session.user, data=_get_update_log_data(updates))
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
        ids = request.form.getlist('session_id', type=int)
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
    PERMISSION = 'contributions'
    object_type = 'contributions'
    hidden_post_field = 'contribution_id'

    def _get_objects(self):
        ids = request.form.getlist('contribution_id', type=int)
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


class RHProgramCodesAPIContributions(RHManageEventBase):
    """RESTful API to bulk-update contribution codes."""

    def _process_GET(self):
        return jsonify({c.friendly_id: c.code for c in self.event.contributions})

    @use_kwargs({
        'codes': fields.Dict(keys=fields.Int, values=fields.String, required=True)
    })
    def _process_PATCH(self, codes):
        contribs = {c.friendly_id: c
                    for c in Contribution.query.with_parent(self.event).filter(Contribution.friendly_id.in_(codes))}
        if invalid := (codes - contribs.keys()):
            abort(422, messages={'codes': [f'Invalid IDs: {", ".join(map(str, invalid))}']})

        updates = {}
        for friendly_id, code in codes.items():
            contrib = contribs[friendly_id]
            if code != contrib.code:
                updates[contrib] = (contrib.code, code)
                contrib.code = code

        self.event.log(EventLogRealm.management, LogKind.change, 'Program',
                       'Program codes assigned to contributions',
                       session.user, data=_get_update_log_data(updates))
        return jsonify({contrib.friendly_id: changes for contrib, changes in updates.items()})

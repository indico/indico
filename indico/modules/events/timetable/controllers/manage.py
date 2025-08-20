# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import dateutil.parser
from flask import jsonify, request, session
from webargs import fields
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from indico.core.db.sqlalchemy.colors import ColorTuple
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.core.errors import UserValueError
from indico.core.marshmallow import mm
from indico.modules.events.contributions import Contribution
from indico.modules.events.contributions.clone import ContributionCloner
from indico.modules.events.contributions.controllers.management import (RHManageContributionBase,
                                                                        RHManageContributionsBase)
from indico.modules.events.contributions.models.references import ContributionReference
from indico.modules.events.contributions.operations import create_contribution, delete_contribution, update_contribution
from indico.modules.events.management.controllers.base import RHManageEventBase
from indico.modules.events.models.references import ReferenceType
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.operations import delete_session_block, update_session_block
from indico.modules.events.timetable.controllers import (RHManageTimetableBase, RHManageTimetableEntryBase,
                                                         SessionManagementLevel)
from indico.modules.events.timetable.legacy import (TimetableSerializer, serialize_entry_update, serialize_event_info,
                                                    serialize_session)
from indico.modules.events.timetable.models.breaks import Break
from indico.modules.events.timetable.models.entries import TimetableEntryType
from indico.modules.events.timetable.operations import (create_break_entry, create_session_block_entry,
                                                        create_timetable_entry, delete_timetable_entry,
                                                        schedule_contribution, update_break_entry,
                                                        update_timetable_entry)
from indico.modules.events.timetable.schemas import BreakSchema, ContributionSchema, SessionBlockSchema
# TODO: (Ajob) Remove 'new' indications once old timetable is fully replaced
from indico.modules.events.timetable.serializer import TimetableSerializer as TimetableSerializerNew
from indico.modules.events.timetable.serializer import serialize_event_info as serialize_event_info_new
from indico.modules.events.timetable.util import render_entry_info_balloon
from indico.modules.events.timetable.views import WPManageTimetable, WPManageTimetableOld
from indico.modules.events.util import should_show_draft_warning, track_location_changes, track_time_changes
from indico.util.i18n import _
from indico.web.args import use_kwargs, use_rh_args
from indico.web.forms.colors import get_colors
from indico.web.util import jsonify_data


class RHManageTimetable(RHManageTimetableBase):
    """Display timetable management page."""

    session_management_level = SessionManagementLevel.coordinate

    def _process(self):
        event_info = serialize_event_info_new(self.event, management=True, user=session.user)
        # TODO: (Ajob) Rename TimetableSerializerNew to TimetableSerializer and remove the old one
        timetable_data = TimetableSerializerNew(self.event, management=True).serialize_timetable()
        return WPManageTimetable.render_template(
            'management_new.html',
            self.event,
            event_info=event_info,
            show_draft_warning=should_show_draft_warning(self.event),
            timetable_data=timetable_data,
        )


class RHManageTimetableOld(RHManageTimetableBase):
    """Display timetable management page."""

    session_management_level = SessionManagementLevel.coordinate

    def _process(self):
        event_info = serialize_event_info(self.event)
        timetable_data = TimetableSerializer(self.event, management=True).serialize_timetable()
        return WPManageTimetableOld.render_template(
            'management.html',
            self.event,
            event_info=event_info,
            show_draft_warning=should_show_draft_warning(self.event),
            timetable_data=timetable_data,
        )


class RHManageSessionTimetable(RHManageTimetableBase):
    """Display session timetable management page."""

    session_management_level = SessionManagementLevel.coordinate

    def _process(self):
        event_info = serialize_event_info(self.event)
        event_info['timetableSession'] = serialize_session(self.session)
        timetable_data = TimetableSerializer(self.event, management=True).serialize_session_timetable(self.session)
        management_rights = {
            'can_manage_event': self.event.can_manage(session.user),
            'can_manage_session': self.session.can_manage(session.user),
            'can_manage_blocks': self.session.can_manage_blocks(session.user),
            'can_manage_contributions': self.session.can_manage_contributions(session.user),
        }
        return WPManageTimetable.render_template(
            'session_management.html',
            self.event,
            event_info=event_info,
            timetable_data=timetable_data,
            session_=self.session,
            **management_rights,
        )


class RHTimetableREST(RHManageTimetableEntryBase):
    """RESTful timetable actions."""

    def _get_contribution_updates(self, data):
        updates = {'parent': None}
        contribution = Contribution.query.with_parent(self.event).filter_by(id=data['contribution_id']).first()
        if contribution is None:
            raise BadRequest('Invalid contribution id')
        elif contribution.timetable_entry is not None:
            raise BadRequest('The contribution is already scheduled')
        updates['object'] = contribution
        if data.get('session_block_id'):
            session_block = self.event.get_session_block(data['session_block_id'])
            if session_block is None:
                raise BadRequest('Invalid session block id')
            if session_block.timetable_entry is None:
                raise BadRequest('The session block is not scheduled')
            if contribution.session and session_block.session != contribution.session and not data.get('force'):
                raise BadRequest('Contribution is assigned to another session')
            updates['parent'] = session_block.timetable_entry
            contribution.session = session_block.session
        else:
            updates['object'].session = None

        return updates

    def _process_POST(self):
        """Create new timetable entry."""
        data = request.json
        required_keys = {'start_dt'}
        allowed_keys = {'start_dt', 'contribution_id', 'session_block_id', 'force'}
        if set(data.keys()) > allowed_keys:
            raise BadRequest('Invalid keys found')
        elif required_keys > set(data.keys()):
            raise BadRequest('Required keys missing')
        updates = {'start_dt': dateutil.parser.parse(data['start_dt'])}
        if 'contribution_id' in data:
            updates.update(self._get_contribution_updates(data))
        # TODO: breaks & session blocks
        else:
            raise BadRequest('No object specified')
        entry = create_timetable_entry(self.event, updates)
        return jsonify(start_dt=entry.start_dt.isoformat(), id=entry.id)

    def _process_PATCH(self):
        """Update a timetable entry."""
        data = request.json
        # TODO: support breaks
        if set(data.keys()) > {'start_dt'}:
            raise BadRequest('Invalid keys found')
        updates = {}
        if 'start_dt' in data:
            updates['start_dt'] = dateutil.parser.parse(data['start_dt'])
        if updates:
            with track_time_changes():
                update_timetable_entry(self.entry, updates)
        return jsonify()

    def _process_DELETE(self):
        """Delete a timetable entry."""
        if self.entry.type == TimetableEntryType.SESSION_BLOCK:
            delete_session_block(self.entry.session_block)
        elif self.event.type != 'conference' and self.entry.type == TimetableEntryType.CONTRIBUTION:
            delete_contribution(self.entry.contribution)
        else:
            delete_timetable_entry(self.entry)


# TODO: (Ajob) Full rest API endpoint


class RHTimetableBreakCreate(RHManageEventBase):
    @use_rh_args(BreakSchema)
    def _process_POST(self, data: Break):
        break_entry = create_break_entry(self.event, data, extend_parent=False)
        return BreakSchema(context={'event': self.event}).jsonify(break_entry.break_)


class RHTimetableBreak(RHManageEventBase):
    def _process_args(self):
        RHManageEventBase._process_args(self)
        self.break_ = Break.query.filter_by(id=request.view_args['break_id']).one()

    @use_rh_args(BreakSchema, partial=True)
    def _process_PATCH(self, data):
        with (track_time_changes(), track_location_changes()):
            update_break_entry(self.break_, data)

        return BreakSchema(context={'event': self.event}).jsonify(self.break_)

    def _process_GET(self):
        return BreakSchema(context={'event': self.event}).jsonify(self.break_)

    def _process_DELETE(self):
        delete_timetable_entry(self.break_.timetable_entry)
        return '', 204


class RHTimetableContributionCreate(RHManageContributionsBase):
    @use_rh_args(ContributionSchema)
    def _process_POST(self, data):
        print(data)
        if (references := data.get('references')) is not None:
            data['references'] = self._get_references(references)
        # TODO: quick hack to get the person_link data in the right format
        data['person_link_data'] = {v['person_link']: v['is_submitter'] for v in data.pop('person_links', [])}
        session_block = SessionBlock.get(data['session_block_id']) if data.get('session_block_id') else None
        data['location_data'] = (
            self._get_inherited_location(location_parent=session_block)
            if data['location_data'].get('inheriting')
            else data['location_data']
        )
        contrib = create_contribution(self.event, data, session_block=session_block)
        return ContributionSchema(context={'event': self.event}).jsonify(contrib)

    @no_autoflush
    def _get_references(self, data: list[dict]) -> list[ContributionReference]:
        references = []
        for entry in data:
            reference_type = ReferenceType.get(entry['reference_type_id'])
            if not reference_type:
                raise BadRequest('Invalid reference type')
            references.append(ContributionReference(reference_type=reference_type, contribution=self.contrib,
                                                    value=entry['value']))
        return references

    def _get_inherited_location(self, **kwargs):
        location_parent = kwargs.pop('location_parent', None)
        inherited_location = location_parent.location_data if location_parent else self.event.location_data
        inherited_location['inheriting'] = True
        return inherited_location


class RHTimetableContribution(RHManageContributionBase):
    @use_rh_args(ContributionSchema, partial=True)
    def _process_PATCH(self, data):
        if (references := data.get('references')) is not None:
            data['references'] = self._get_references(references)

        data['person_link_data'] = {v['person_link']: v['is_submitter'] for v in data.pop('person_links', [])}

        with (track_time_changes(), track_location_changes()):
            update_contribution(self.contrib, data)

        return ContributionSchema(context={'event': self.event}).jsonify(self.contrib)

    def _process_GET(self):
        return ContributionSchema(context={'event': self.event}).jsonify(self.contrib)

    def _process_DELETE(self):
        delete_timetable_entry(self.contrib.timetable_entry)
        return '', 204

    @no_autoflush
    def _get_references(self, data: list[dict]) -> list[ContributionReference]:
        references = []
        for entry in data:
            reference_type = ReferenceType.get(entry['reference_type_id'])
            if not reference_type:
                raise BadRequest('Invalid reference type')
            references.append(ContributionReference(reference_type=reference_type, contribution=self.contrib,
                                                    value=entry['value']))
        return references


class RHTimetableScheduleContribution(RHManageTimetableBase):
    session_management_level = SessionManagementLevel.coordinate

    class ScheduleContribSchema(mm.Schema):
        contrib_id = fields.Int(required=True)
        start_dt = fields.DateTime(required=True)

    @use_kwargs({
        'block_id': fields.Int(load_default=None),
    }, location='view_args')
    def _process_args(self, block_id):
        RHManageTimetableBase._process_args(self)
        self.session_block = None
        if block_id is not None:
            self.session_block = self.event.get_session_block(request.view_args['block_id'])
            if self.session_block is None:
                raise NotFound
            if self.session and self.session != self.session_block.session:
                raise BadRequest

    @use_kwargs({
        'contribs': fields.List(fields.Nested(ScheduleContribSchema), required=True),
    })
    def _process(self, contribs):
        contrib_map = {c['contrib_id']: c['start_dt'] for c in contribs}
        query = (
            Contribution
                .query.with_parent(self.event)
                .filter(Contribution.id.in_(contrib_map.keys()))
        )

        with track_time_changes():
            for contrib in query:
                if self.session and contrib.session_id != self.session.id:
                    # TODO(tomas): Allow scheduling contributions assigned to other sessions?
                    raise Forbidden('Contribution not assigned to this session')

                start_dt = contrib_map[contrib.id]
                entry = schedule_contribution(contrib, start_dt, session_block=self.session_block,
                                              extend_parent=False)
                if entry.end_dt.astimezone(entry.event.tzinfo).date() > start_dt.date():
                    raise UserValueError(_("Contribution '{}' could not be scheduled since it doesn't fit on this day.")
                                         .format(contrib.title))
        return '', 204


class RHTimetableSessionBlockCreate(RHManageEventBase):
    @use_rh_args(SessionBlockSchema)
    def _process_POST(self, data: SessionBlockSchema):
        session = self.event.get_session(data['session_id'])

        if not session:
            raise NotFound

        block_entry = create_session_block_entry(session, data, extend_parent=False)
        return SessionBlockSchema(context={'event': self.event}).jsonify(block_entry.session_block)


class RHTimetableSessionBlock(RHManageEventBase):
    def _process_args(self):
        RHManageEventBase._process_args(self)
        self.session_block = SessionBlock.query.filter_by(id=request.view_args['session_block_id']).one()

    @use_rh_args(SessionBlockSchema, partial=True)
    def _process_PATCH(self, data):
        with (track_time_changes(), track_location_changes()):
            update_session_block(self.session_block, data)

        return SessionBlockSchema(context={'event': self.event}).jsonify(self.session_block)

    def _process_GET(self):
        return SessionBlockSchema(context={'event': self.event}).jsonify(self.session_block)

    def _process_DELETE(self):
        delete_session_block(self.session_block)
        return '', 204

# END OF REST API


class RHManageTimetableEntryInfo(RHManageTimetableEntryBase):
    """Display timetable entry info balloon in management mode."""

    session_management_level = SessionManagementLevel.coordinate

    def _process_args(self):
        RHManageTimetableEntryBase._process_args(self)
        self.is_session_timetable = request.args.get('is_session_timetable') == '1'
        if not self.entry:
            raise NotFound

    def _process(self):
        html = render_entry_info_balloon(self.entry, editable=True, sess=self.session,
                                         is_session_timetable=self.is_session_timetable)
        return jsonify(html=html)


class RHBreakREST(RHManageTimetableBase):
    """RESTful operations for managing breaks."""

    def _process_args(self):
        RHManageTimetableBase._process_args(self)
        self.entry = self.event.timetable_entries.filter_by(break_id=request.view_args['break_id']).first_or_404()
        self.break_ = self.entry.break_

    def _check_access(self):
        if not self.entry.parent or self.entry.parent.type != TimetableEntryType.SESSION_BLOCK:
            RHManageTimetableBase._check_access(self)
        elif not self.entry.parent.session_block.session.can_manage(session.user, permission='coordinate'):
            raise Forbidden

    def _process_PATCH(self):
        data = request.json
        if set(data.keys()) > {'colors'}:
            raise BadRequest
        if 'colors' in data:
            colors = ColorTuple(**data['colors'])
            if colors not in get_colors():
                raise BadRequest
            self.break_.colors = colors


class RHCloneContribution(RHManageTimetableBase):
    """Clone a contribution and schedule it at the same position."""

    def _process_args(self):
        RHManageTimetableBase._process_args(self)
        self.contrib = (Contribution.query.with_parent(self.event)
                .filter_by(id=request.args['contrib_id'])
                .one())

    def _process(self):
        contrib = ContributionCloner.clone_single_contribution(self.contrib, preserve_session=True)
        return jsonify_data(update=serialize_entry_update(contrib.timetable_entry, session_=contrib.session))

# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import jsonify, request, session
from sqlalchemy.orm import subqueryload, undefer
from werkzeug.exceptions import BadRequest

from indico.core.db import db
from indico.core.db.sqlalchemy.colors import ColorTuple
from indico.core.db.sqlalchemy.protection import ProtectionMode, render_acl
from indico.core.permissions import get_principal_permissions, update_permissions
from indico.modules.events import EventLogKind, EventLogRealm
from indico.modules.events.contributions import contribution_settings
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.management.controllers.base import RHContributionPersonListMixin
from indico.modules.events.sessions.controllers.management import (RHManageSessionBase, RHManageSessionsActionsBase,
                                                                   RHManageSessionsBase)
from indico.modules.events.sessions.forms import (MeetingSessionBlockForm, SessionForm, SessionProtectionForm,
                                                  SessionTypeForm)
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.sessions.models.types import SessionType
from indico.modules.events.sessions.operations import (create_session, delete_session, update_session,
                                                       update_session_block)
from indico.modules.events.sessions.util import (generate_pdf_from_sessions, generate_spreadsheet_from_sessions,
                                                 render_session_type_row)
from indico.modules.events.sessions.views import WPManageSessions
from indico.modules.events.util import get_random_color
from indico.util.spreadsheets import send_csv, send_xlsx
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import send_file
from indico.web.forms.base import FormDefaults
from indico.web.forms.colors import get_colors
from indico.web.forms.fields.principals import serialize_principal
from indico.web.forms.util import get_form_field_names
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


def _get_session_list_args(event):
    sessions = (Session.query.with_parent(event)
                .options(undefer('attachment_count'),
                         subqueryload('blocks').undefer('contribution_count'))
                .order_by(db.func.lower(Session.title))
                .all())
    types = [{'id': t.id, 'title': t.name} for t in event.session_types]
    return {'sessions': sessions, 'default_colors': get_colors(), 'types': types}


def _render_session_list(event):
    tpl = get_template_module('events/sessions/management/_session_list.html')
    return tpl.render_session_list(event, **_get_session_list_args(event))


class RHSessionsList(RHManageSessionsBase):
    """Display list of all sessions within the event"""

    def _process(self):
        selected_entry = request.args.get('selected')
        selected_entry = int(selected_entry) if selected_entry else None
        return WPManageSessions.render_template('management/session_list.html', self.event,
                                                selected_entry=selected_entry,
                                                **_get_session_list_args(self.event))


class RHCreateSession(RHManageSessionsBase):
    """Create a session in the event"""

    def _get_response(self, new_session):
        sessions = [{'id': s.id, 'title': s.title, 'colors': s.colors} for s in self.event.sessions]
        return jsonify_data(sessions=sessions, new_session_id=new_session.id,
                            html=_render_session_list(self.event))

    def _process(self):
        inherited_location = self.event.location_data
        inherited_location['inheriting'] = True
        default_duration = contribution_settings.get(self.event, 'default_duration')
        form = SessionForm(obj=FormDefaults(colors=get_random_color(self.event), location_data=inherited_location,
                                            default_contribution_duration=default_duration),
                           event=self.event)
        if form.validate_on_submit():
            new_session = create_session(self.event, form.data)
            return self._get_response(new_session)
        return jsonify_form(form)


class RHModifySession(RHManageSessionBase):
    """Modify a session"""

    def _process(self):
        form = SessionForm(obj=self.session, event=self.event)
        if form.validate_on_submit():
            update_session(self.session, form.data)
            return jsonify_data(html=_render_session_list(self.event))
        return jsonify_form(form)


class RHDeleteSessions(RHManageSessionsActionsBase):
    """Remove multiple sessions"""

    def _process(self):
        for sess in self.sessions:
            delete_session(sess)
        return jsonify_data(html=_render_session_list(self.event))


class RHManageSessionsExportBase(RHManageSessionsActionsBase):
    ALLOW_LOCKED = True


class RHExportSessionsCSV(RHManageSessionsExportBase):
    """Export list of sessions to a CSV"""

    def _process(self):
        headers, rows = generate_spreadsheet_from_sessions(self.sessions)
        return send_csv('sessions.csv', headers, rows)


class RHExportSessionsExcel(RHManageSessionsExportBase):
    """Export list of sessions to a XLSX"""

    def _process(self):
        headers, rows = generate_spreadsheet_from_sessions(self.sessions)
        return send_xlsx('sessions.xlsx', headers, rows)


class RHExportSessionsPDF(RHManageSessionsExportBase):
    """Export list of sessions to a PDF"""

    def _process(self):
        pdf_file = generate_pdf_from_sessions(self.sessions)
        return send_file('sessions.pdf', pdf_file, 'application/pdf')


class RHSessionREST(RHManageSessionBase):
    """Perform update or removal of a session"""

    def _process_DELETE(self):
        delete_session(self.session)
        return jsonify_data(html=_render_session_list(self.event))

    def _process_PATCH(self):
        data = request.json
        updates = {}
        if set(data) - {'colors', 'type_id'}:
            raise BadRequest
        if 'colors' in data:
            colors = ColorTuple(**data['colors'])
            if colors not in get_colors():
                raise BadRequest
            updates['colors'] = colors
        if 'type_id' in data:
            updates.update(self._get_session_type_updates(data['type_id']))
        update_session(self.session, updates)
        return jsonify()

    def _get_session_type_updates(self, type_id):
        updates = {}
        if type_id is None:
            updates['type'] = None
        else:
            type_ = SessionType.query.with_parent(self.event).filter_by(id=type_id).first()
            if not type_:
                raise BadRequest('Invalid type id')
            if not self.session.type or type_id != self.session.type.id:
                updates['type'] = type_
        return updates


class RHSessionPersonList(RHContributionPersonListMixin, RHManageSessionsActionsBase):
    """List of persons in the session's contributions"""

    template = 'events/sessions/management/session_person_list.html'
    ALLOW_LOCKED = True

    @property
    def _membership_filter(self):
        session_ids = {s.id for s in self.sessions}
        return Contribution.session_id.in_(session_ids)


class RHSessionProtection(RHManageSessionBase):
    """Manage session protection"""

    def _process(self):
        form = SessionProtectionForm(obj=FormDefaults(**self._get_defaults()), session=self.session,
                                     prefix='session-protection-')
        if form.validate_on_submit():
            update_permissions(self.session, form)
            update_session(self.session, {'protection_mode': form.protection_mode.data})
            return jsonify_data(flash=False, html=_render_session_list(self.event))
        return jsonify_template('events/management/protection_dialog.html', form=form)

    def _get_defaults(self):
        permissions = [[serialize_principal(p.principal), list(get_principal_permissions(p, Session))]
                       for p in self.session.acl_entries]
        permissions = [item for item in permissions if item[1]]
        return {'permissions': permissions, 'protection_mode': self.session.protection_mode}


class RHSessionACL(RHManageSessionBase):
    """Display the ACL of the session"""

    def _process(self):
        return render_acl(self.session)


class RHSessionACLMessage(RHManageSessionBase):
    """Render the inheriting ACL message"""

    def _process(self):
        mode = ProtectionMode[request.args['mode']]
        return jsonify_template('forms/protection_field_acl_message.html', object=self.session, mode=mode,
                                endpoint='sessions.acl')


class RHManageSessionBlock(RHManageSessionBase):
    """Manage a block of a session"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.session_block
        }
    }

    def _process_args(self):
        RHManageSessionBase._process_args(self)
        self.session_block = SessionBlock.get_or_404(request.view_args['block_id'])

    def _process(self):
        form = MeetingSessionBlockForm(obj=FormDefaults(**self._get_form_defaults()), event=self.event,
                                       session_block=self.session_block)
        if form.validate_on_submit():
            session_data = {k[8:]: v for k, v in form.data.iteritems() if k in form.session_fields}
            block_data = {k[6:]: v for k, v in form.data.iteritems() if k in form.block_fields}
            update_session(self.session, session_data)
            update_session_block(self.session_block, block_data)
            return jsonify_data(flash=False)
        self.commit = False
        return jsonify_template('events/forms/session_block_form.html', form=form, block=self.session_block)

    def _get_form_defaults(self):
        fields = get_form_field_names(MeetingSessionBlockForm)
        defaults = {}
        defaults.update((name, getattr(self.session, name[8:])) for name in fields if name.startswith('session_'))
        defaults.update((name, getattr(self.session_block, name[6:])) for name in fields if name.startswith('block_'))
        return defaults


class RHSessionBlocks(RHManageSessionBase):
    def _process(self):
        return jsonify_template('events/sessions/management/session_blocks.html', sess=self.session)


class RHManageSessionTypes(RHManageSessionsBase):
    """Dialog to manage the session types of an event"""

    def _process(self):
        return jsonify_template('events/sessions/management/types_dialog.html', event=self.event,
                                types=self.event.session_types)


class RHManageSessionTypeBase(RHManageSessionsBase):
    """Manage a session type of an event"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.session_type
        }
    }

    def _process_args(self):
        RHManageSessionsBase._process_args(self)
        self.session_type = SessionType.get_or_404(request.view_args['session_type_id'])


class RHEditSessionType(RHManageSessionTypeBase):
    """Dialog to edit a SessionType"""

    def _process(self):
        form = SessionTypeForm(event=self.event, obj=self.session_type)
        if form.validate_on_submit():
            old_name = self.session_type.name
            form.populate_obj(self.session_type)
            db.session.flush()
            self.event.log(EventLogRealm.management, EventLogKind.change, 'Sessions',
                           'Updated type: {}'.format(old_name), session.user)
            return jsonify_data(html_row=render_session_type_row(self.session_type), flash=False)
        return jsonify_form(form)


class RHCreateSessionType(RHManageSessionsBase):
    """Dialog to add a SessionType"""

    def _process(self):
        form = SessionTypeForm(event=self.event)
        if form.validate_on_submit():
            session_type = SessionType()
            form.populate_obj(session_type)
            self.event.session_types.append(session_type)
            db.session.flush()
            self.event.log(EventLogRealm.management, EventLogKind.positive, 'Sessions',
                           'Added type: {}'.format(session_type.name), session.user)
            types = [{'id': t.id, 'title': t.name} for t in self.event.session_types]
            return jsonify_data(types=types, new_type_id=session_type.id,
                                html_row=render_session_type_row(session_type))
        return jsonify_form(form)


class RHDeleteSessionType(RHManageSessionTypeBase):
    """Dialog to delete a SessionType"""

    def _process(self):
        db.session.delete(self.session_type)
        db.session.flush()
        self.event.log(EventLogRealm.management, EventLogKind.negative, 'Sessions',
                       'Deleted type: {}'.format(self.session_type.name), session.user)
        return jsonify_data(flash=False)

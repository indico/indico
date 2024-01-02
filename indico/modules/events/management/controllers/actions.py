# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import flash, request, session
from webargs import fields
from werkzeug.exceptions import Forbidden, NotFound

from indico.modules.categories.models.categories import Category
from indico.modules.events.management.controllers.base import RHManageEventBase
from indico.modules.events.models.events import EventType
from indico.modules.events.notifications import notify_move_request_creation
from indico.modules.events.operations import create_event_request, lock_event, unlock_event, update_event_type
from indico.util.i18n import _
from indico.util.marshmallow import ModelField
from indico.web.args import use_kwargs
from indico.web.flask.util import url_for
from indico.web.util import jsonify_data, jsonify_template, url_for_index


class RHDeleteEvent(RHManageEventBase):
    """Delete an event."""

    def _process_GET(self):
        return jsonify_template('events/management/delete_event.html', event=self.event)

    def _process_POST(self):
        self.event.delete('Deleted by user', session.user)
        flash(_('Event "{}" successfully deleted.').format(self.event.title), 'success')
        category = self.event.category

        if category and category.can_manage(session.user):
            redirect_url = url_for('categories.manage_content', category)
        elif category and category.can_access(session.user):
            redirect_url = url_for('categories.display', category)
        else:
            redirect_url = url_for_index()
        return jsonify_data(flash=False, redirect=redirect_url)


class RHChangeEventType(RHManageEventBase):
    """Change the type of an event."""

    def _process(self):
        type_ = EventType[request.form['type']]
        update_event_type(self.event, type_)
        flash(_('The event type has been changed to {}.').format(type_.title), 'success')
        return jsonify_data(flash=False, redirect=url_for('.settings', self.event))


class RHLockEvent(RHManageEventBase):
    """Lock an event."""

    def _check_access(self):
        RHManageEventBase._check_access(self)
        if not self.event.can_lock(session.user):
            raise Forbidden

    def _process_GET(self):
        return jsonify_template('events/management/lock_event.html')

    def _process_POST(self):
        lock_event(self.event)
        flash(_('The event is now locked.'), 'success')
        return jsonify_data(flash=False)


class RHUnlockEvent(RHManageEventBase):
    """Unlock an event."""

    def _check_access(self):
        self.ALLOW_LOCKED = self.event.can_lock(session.user)
        RHManageEventBase._check_access(self)

    def _process(self):
        unlock_event(self.event)
        flash(_('The event is now unlocked.'), 'success')
        return jsonify_data(flash=False)


class RHMoveEvent(RHManageEventBase):
    """Move event to a different category."""

    @use_kwargs({
        'target_category': ModelField(Category, filter_deleted=True, required=True, data_key='target_category_id'),
        'comment': fields.String(load_default=''),
    })
    def _process_args(self, target_category, comment):
        RHManageEventBase._process_args(self)
        self.target_category = target_category
        self.comment = comment

    def _check_access(self):
        RHManageEventBase._check_access(self)
        if (not self.target_category.can_create_events(session.user)
                and not self.target_category.can_propose_events(session.user)):
            raise Forbidden(_('You may not move events to this category.'))

    def _process(self):
        if self.target_category.can_create_events(session.user):
            self.event.move(self.target_category)
            flash(_('Event "{event}" has been moved to category "{category}"')
                  .format(event=self.event.title, category=self.target_category.title),
                  'success')
        else:
            create_event_request(self.event, self.target_category, self.comment)
            notify_move_request_creation([self.event], self.target_category, self.comment)
            flash(_('Moving the event "{event}" to "{category}" has been requested and is pending approval')
                  .format(event=self.event.title, category=self.target_category.title),
                  'success')
        return jsonify_data(flash=False)


class RHWithdrawMoveRequest(RHManageEventBase):
    """Withdraw a move request."""

    def _process_args(self):
        RHManageEventBase._process_args(self)
        self.request = self.event.pending_move_request
        if not self.request:
            raise NotFound

    def _process(self):
        self.request.withdraw(user=session.user)
        flash(_('The move request has been withdrawn'), 'success')
        return jsonify_data(flash=False)

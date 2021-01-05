# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import flash, request, session
from werkzeug.exceptions import Forbidden

from indico.modules.categories.models.categories import Category
from indico.modules.events.management.controllers.base import RHManageEventBase
from indico.modules.events.models.events import EventType
from indico.modules.events.operations import lock_event, unlock_event, update_event_type
from indico.util.i18n import _
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
        if category.can_manage(session.user):
            redirect_url = url_for('categories.manage_content', category)
        elif category.can_access(session.user):
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

    def _process_args(self):
        RHManageEventBase._process_args(self)
        self.target_category = Category.get_or_404(int(request.form['target_category_id']), is_deleted=False)
        if not self.target_category.can_create_events(session.user):
            raise Forbidden(_("You may only move events to categories where you are allowed to create events."))

    def _process(self):
        self.event.move(self.target_category)
        flash(_('Event "{}" has been moved to category "{}"').format(self.event.title, self.target_category.title),
              'success')
        return jsonify_data(flash=False)

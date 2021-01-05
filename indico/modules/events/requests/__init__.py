# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import session

from indico.core import signals
from indico.modules.events.requests.base import RequestDefinitionBase, RequestFormBase
from indico.modules.events.requests.util import get_request_definitions, is_request_manager
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


__all__ = ('RequestDefinitionBase', 'RequestFormBase')


@signals.app_created.connect
def _check_request_definitions(app, **kwargs):
    # This will raise RuntimeError if the request type names are not unique
    get_request_definitions()


@signals.menu.items.connect_via('event-management-sidemenu')
def _extend_event_management_menu(sender, event, **kwargs):
    if not get_request_definitions():
        return
    if not event.can_manage(session.user) and not is_request_manager(session.user):
        return
    return SideMenuItem('requests', _('Logistics'), url_for('requests.event_requests', event), section='services')


@signals.event_management.management_url.connect
def _get_event_management_url(event, **kwargs):
    if is_request_manager(session.user):
        return url_for('requests.event_requests', event)


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    from indico.modules.events.requests.models.requests import Request
    Request.find(created_by_id=source.id).update({Request.created_by_id: target.id})
    Request.find(processed_by_id=source.id).update({Request.processed_by_id: target.id})


@signals.event.deleted.connect
def _event_deleted(event, **kwargs):
    from indico.modules.events.requests.models.requests import Request, RequestState
    query = (Request.query.with_parent(event)
             .filter(Request.state.in_((RequestState.accepted, RequestState.pending))))
    for req in query:
        req.definition.withdraw(req, notify_event_managers=False)

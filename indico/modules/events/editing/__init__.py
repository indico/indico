# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import session

from indico.core import signals
from indico.core.logger import Logger
from indico.core.permissions import ManagementPermission
from indico.modules.events.features.base import EventFeature
from indico.modules.events.models.events import Event, EventType
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('events.editing')


class EditingFeature(EventFeature):
    name = 'editing'
    friendly_name = _('Paper Editing')
    description = _('Gives event managers the opportunity to let contributors submit papers to be edited and '
                    'eventually published.')

    @classmethod
    def is_allowed_for_event(cls, event):
        return event.type_ == EventType.conference


@signals.event.get_feature_definitions.connect
def _get_feature_definitions(sender, **kwargs):
    return EditingFeature


@signals.acl.get_management_permissions.connect_via(Event)
def _get_management_permissions(sender, **kwargs):
    yield EditableEditorPermission


@signals.menu.items.connect_via('event-management-sidemenu')
def _extend_event_management_menu(sender, event, **kwargs):
    if not event.can_manage(session.user) or not EditingFeature.is_allowed_for_event(event):
        return
    return SideMenuItem('editing', _('Paper Editing'), url_for('event_editing.dashboard', event),
                        section='organization')


class EditableEditorPermission(ManagementPermission):
    name = 'paper_editing'
    friendly_name = _('Paper Editor')
    description = _('Grants editor rights for paper editing on an event.')
    user_selectable = True

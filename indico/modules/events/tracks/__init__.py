# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import session

from indico.core import signals
from indico.core.logger import Logger
from indico.core.permissions import ManagementPermission
from indico.modules.events import Event
from indico.modules.events.models.events import EventType
from indico.modules.events.tracks.clone import TrackCloner
from indico.modules.events.tracks.models.tracks import Track
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('tracks')


@signals.menu.items.connect_via('event-management-sidemenu')
def _sidemenu_items(sender, event, **kwargs):
    if event.type_ == EventType.conference and event.can_manage(session.user):
        return SideMenuItem('program', _('Programme'), url_for('tracks.manage', event), section='organization')


@signals.event.sidemenu.connect
def _extend_event_menu(sender, **kwargs):
    from indico.modules.events.layout.util import MenuEntryData
    from indico.modules.events.tracks.settings import track_settings

    def _program_visible(event):
        return bool(track_settings.get(event, 'program').strip() or Track.query.with_parent(event).has_rows())

    return MenuEntryData(title=_("Scientific Programme"), name='program', endpoint='tracks.program', position=1,
                         visible=_program_visible, static_site=True)


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    target.abstract_reviewer_for_tracks |= source.abstract_reviewer_for_tracks
    source.abstract_reviewer_for_tracks.clear()
    target.convener_for_tracks |= source.convener_for_tracks
    source.convener_for_tracks.clear()


@signals.event_management.get_cloners.connect
def _get_cloners(sender, **kwargs):
    yield TrackCloner


@signals.acl.get_management_permissions.connect_via(Event)
def _get_management_permissions(sender, **kwargs):
    return TrackConvenerPermission


class TrackConvenerPermission(ManagementPermission):
    name = 'track_convener'
    friendly_name = _('Track convener')
    description = _('Grants track convener rights in an event')

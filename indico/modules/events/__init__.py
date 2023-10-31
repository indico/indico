# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re

from flask import flash, redirect, request, session
from werkzeug.exceptions import BadRequest, NotFound

from indico.core import signals
from indico.core.db.sqlalchemy.protection import make_acl_log_fn
from indico.core.logger import Logger
from indico.core.permissions import ManagementPermission, check_permissions
from indico.modules.events.cloning import get_event_cloners
from indico.modules.events.management.settings import privacy_settings
from indico.modules.events.models.events import Event
from indico.modules.events.models.legacy_mapping import LegacyEventMapping
from indico.modules.logs import EventLogRealm
from indico.util.i18n import _, ngettext
from indico.util.string import is_legacy_id
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem, TopMenuItem, TopMenuSection


__all__ = ('Event', 'logger', 'event_management_object_url_prefixes', 'event_object_url_prefixes')
logger = Logger.get('events')

#: URL prefixes for the various event objects (public area)
#: All prefixes are expected to be used inside the '/event/<int:event_id>'
#: url space.
event_object_url_prefixes = {
    'event': [''],
    'session': ['/sessions/<int:session_id>'],
    'contribution': ['/contributions/<int:contrib_id>'],
    'subcontribution': ['/contributions/<int:contrib_id>/subcontributions/<int:subcontrib_id>']
}

#: URL prefixes for the various event objects (management area)
#: All prefixes are expected to be used inside the '/event/<int:event_id>'
#: url space.
event_management_object_url_prefixes = {
    'event': ['/manage'],
    'session': ['/manage/sessions/<int:session_id>'],
    'contribution': ['/manage/contributions/<int:contrib_id>'],
    'subcontribution': ['/manage/contributions/<int:contrib_id>/subcontributions/<int:subcontrib_id>']
}

# Log ACL changes
signals.acl.entry_changed.connect(make_acl_log_fn(Event, EventLogRealm.management), sender=Event, weak=False)


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    from indico.modules.events.models.persons import EventPerson
    from indico.modules.events.models.principals import EventPrincipal
    EventPerson.merge_users(target, source)
    EventPrincipal.merge_users(target, source, 'event')
    target.event_roles |= source.event_roles
    source.event_roles.clear()


@signals.users.registered.connect
@signals.users.email_added.connect
def _convert_email_principals(user, silent=False, **kwargs):
    from indico.modules.events.models.principals import EventPrincipal
    events = EventPrincipal.replace_email_with_user(user, 'event')
    if events and not silent:
        num = len(events)
        flash(ngettext('You have been granted manager/submission privileges for an event.',
                       'You have been granted manager/submission privileges for {} events.', num).format(num), 'info')


@signals.users.registered.connect
@signals.users.email_added.connect
def _convert_email_person_links(user, **kwargs):
    from indico.modules.events.models.persons import EventPerson
    EventPerson.link_user_by_email(user)


@signals.core.app_created.connect
def _handle_legacy_ids(app, **kwargs):
    """
    Handle the redirect from broken legacy event ids such as a12345
    or 0123 which cannot be converted to an integer without an error
    or losing relevant information (0123 and 123 may be different
    events).
    """

    # Endpoints which need to deal with non-standard event "ids" because they might be shorturls.
    # Those endpoints handle legacy event ids on their own so we ignore them here.
    _non_standard_id_endpoints = {
        'events.shorturl', 'events.display', 'events.display_overview',
        'events.create', 'events.prepare',
    }

    # Match event ids which are either not purely numeric or have a leading zero without being exactly `0`
    _legacy_event_id_re = re.compile(r'/event/((?=0[^/]|\d*[^\d/])[^/]*)')

    @app.before_request
    def _redirect_legacy_id():
        if request.endpoint in _non_standard_id_endpoints:
            return

        if not (match := _legacy_event_id_re.match(request.path)):
            return

        event_id = match.group(1)
        assert is_legacy_id(event_id)

        if request.method != 'GET':
            raise BadRequest('Unexpected non-GET request with legacy event ID')

        mapping = LegacyEventMapping.query.filter_by(legacy_event_id=event_id).first()
        if mapping is None:
            raise NotFound(f'Legacy event {event_id} does not exist')

        new_url = _legacy_event_id_re.sub(f'/event/{mapping.event_id}', request.url, count=1)
        return redirect(new_url, 302 if app.debug else 301)


@signals.core.app_created.connect
def _check_permissions(app, **kwargs):
    check_permissions(Event)


@signals.acl.get_management_permissions.connect_via(Event)
def _get_management_permissions(sender, **kwargs):
    return SubmitterPermission


class SubmitterPermission(ManagementPermission):
    name = 'submit'
    friendly_name = _('Submission')
    description = _('Grants management rights for event-wide materials and minutes.')
    user_selectable = True


@signals.menu.items.connect_via('admin-sidemenu')
def _sidemenu_items(sender, **kwargs):
    if session.user.is_admin:
        yield SideMenuItem('reference_types', _('External ID Types'), url_for('events.reference_types'),
                           section='customization')
        yield SideMenuItem('event_labels', _('Event Labels'), url_for('events.event_labels'),
                           section='customization')
        yield SideMenuItem('unlisted_events', _('Unlisted events'), url_for('events.unlisted_events'),
                           section='customization')
        yield SideMenuItem('autolinker', _('Auto-linker'), url_for('events.autolinker_admin'),
                           section='customization')


@signals.menu.sections.connect_via('top-menu')
def _topmenu_sections(sender, **kwargs):
    yield TopMenuSection('create-event', _('Create event'), 90)


@signals.menu.items.connect_via('top-menu')
def _topmenu_items(sender, **kwargs):
    yield TopMenuItem('create-lecture', _('Create lecture'), 'lecture', 30, section='create-event')
    yield TopMenuItem('create-meeting', _('Create meeting'), 'meeting', 20, section='create-event')
    yield TopMenuItem('create-conference', _('Create conference'), 'conference', 10, section='create-event')


@signals.event.sidemenu.connect
def _extend_event_menu(sender, **kwargs):
    from indico.modules.events.layout.util import MenuEntryData, get_menu_entry_by_name

    def _my_conference_visible(event):
        return session.user and (get_menu_entry_by_name('my_contributions', event).is_visible or
                                 get_menu_entry_by_name('my_sessions', event).is_visible)

    def _visible_privacy_information(event):
        return any(privacy_settings.get_all(event).values())

    yield MenuEntryData(_('Overview'), 'overview', 'events.display_overview', position=0, static_site=True)
    yield MenuEntryData(_('My Conference'), 'my_conference', position=7, visible=_my_conference_visible)
    yield MenuEntryData(_('Privacy Information'), 'privacy', 'events.display_privacy', position=13,
                        visible=_visible_privacy_information, static_site=True, hide_if_restricted=False)


@signals.core.app_created.connect
def _check_cloners(app, **kwargs):
    # This will raise RuntimeError if the cloner names are not unique
    get_event_cloners()


@signals.event_management.get_cloners.connect
def _get_cloners(sender, **kwargs):
    from indico.modules.events import clone
    yield clone.EventLocationCloner
    yield clone.EventPersonCloner
    yield clone.EventPersonLinkCloner
    yield clone.EventProtectionCloner
    yield clone.EventSeriesCloner


@signals.event.cloned.connect
def _event_cloned(old_event, new_event, **kwargs):
    new_event.cloned_from = old_event
    new_event.keywords = old_event.keywords
    new_event.organizer_info = old_event.organizer_info
    new_event.additional_info = old_event.additional_info
    new_event.contact_title = old_event.contact_title
    new_event.contact_emails = old_event.contact_emails
    new_event.contact_phones = old_event.contact_phones

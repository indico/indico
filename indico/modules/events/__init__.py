# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from flask import flash, redirect, render_template, request, session
from werkzeug.exceptions import BadRequest, NotFound

from indico.core import signals
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.logger import Logger
from indico.core.roles import ManagementRole, check_roles, get_available_roles
from indico.modules.events.cloning import get_event_cloners
from indico.modules.events.logs import EventLogKind, EventLogRealm
from indico.modules.events.models.events import Event
from indico.modules.events.models.legacy_mapping import LegacyEventMapping
from indico.util.i18n import _, ngettext, orig_string
from indico.util.string import is_legacy_id
from indico.web.flask.templating import template_hook
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem, TopMenuItem, TopMenuSection


__all__ = ('Event', 'logger', 'event_management_object_url_prefixes', 'event_object_url_prefixes')
logger = Logger.get('events')

#: URL prefixes for the various event objects (public area)
#: All prefixes are expected to be used inside the '/event/<confId>'
#: url space.
event_object_url_prefixes = {
    'event': [''],
    'session': ['/sessions/<int:session_id>'],
    'contribution': ['/contributions/<int:contrib_id>'],
    'subcontribution': ['/contributions/<int:contrib_id>/subcontributions/<int:subcontrib_id>']
}

#: URL prefixes for the various event objects (management area)
#: All prefixes are expected to be used inside the '/event/<confId>'
#: url space.
event_management_object_url_prefixes = {
    'event': ['/manage'],
    'session': ['/manage/sessions/<int:session_id>'],
    'contribution': ['/manage/contributions/<int:contrib_id>'],
    'subcontribution': ['/manage/contributions/<int:contrib_id>/subcontributions/<int:subcontrib_id>']
}


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    from indico.modules.events.models.persons import EventPerson
    from indico.modules.events.models.principals import EventPrincipal
    EventPerson.merge_users(target, source)
    EventPrincipal.merge_users(target, source, 'event')


@signals.users.registered.connect
@signals.users.email_added.connect
def _convert_email_principals(user, **kwargs):
    from indico.modules.events.models.principals import EventPrincipal
    events = EventPrincipal.replace_email_with_user(user, 'event')
    if events:
        num = len(events)
        flash(ngettext("You have been granted manager/submission privileges for an event.",
                       "You have been granted manager/submission privileges for {} events.", num).format(num), 'info')


@signals.users.registered.connect
@signals.users.email_added.connect
def _convert_email_person_links(user, **kwargs):
    from indico.modules.events.models.persons import EventPerson
    EventPerson.link_user_by_email(user)


@signals.acl.entry_changed.connect_via(Event)
def _log_acl_changes(sender, obj, principal, entry, is_new, old_data, quiet, **kwargs):
    if quiet:
        return

    available_roles = get_available_roles(Event)

    def _format_roles(roles):
        roles = set(roles)
        return ', '.join(sorted(orig_string(role.friendly_name) for role in available_roles.itervalues()
                                if role.name in roles))

    data = {}
    if principal.principal_type == PrincipalType.user:
        data['User'] = principal.full_name
    elif principal.principal_type == PrincipalType.email:
        data['Email'] = principal.email
    elif principal.principal_type == PrincipalType.local_group:
        data['Group'] = principal.name
    elif principal.principal_type == PrincipalType.multipass_group:
        data['Group'] = '{} ({})'.format(principal.name, principal.provider_title)
    elif principal.principal_type == PrincipalType.network:
        data['IP Network'] = principal.name
    if entry is None:
        data['Read Access'] = old_data['read_access']
        data['Manager'] = old_data['full_access']
        data['Roles'] = _format_roles(old_data['roles'])
        obj.log(EventLogRealm.management, EventLogKind.negative, 'Protection', 'ACL entry removed', session.user,
                data=data)
    elif is_new:
        data['Read Access'] = entry.read_access
        data['Manager'] = entry.full_access
        if entry.roles:
            data['Roles'] = _format_roles(entry.roles)
        obj.log(EventLogRealm.management, EventLogKind.positive, 'Protection', 'ACL entry added', session.user,
                data=data)
    elif entry.current_data != old_data:
        data['Read Access'] = entry.read_access
        data['Manager'] = entry.full_access
        current_roles = set(entry.roles)
        added_roles = current_roles - old_data['roles']
        removed_roles = old_data['roles'] - current_roles
        if added_roles:
            data['Roles (added)'] = _format_roles(added_roles)
        if removed_roles:
            data['Roles (removed)'] = _format_roles(removed_roles)
        if current_roles:
            data['Roles'] = _format_roles(current_roles)
        obj.log(EventLogRealm.management, EventLogKind.change, 'Protection', 'ACL entry changed', session.user,
                data=data)


@signals.app_created.connect
def _handle_legacy_ids(app, **kwargs):
    """
    Handles the redirect from broken legacy event ids such as a12345
    or 0123 which cannot be converted to an integer without an error
    or losing relevant information (0123 and 123 may be different
    events).
    """

    # Endpoints which need to deal with non-standard event "ids" because they might be shorturls.
    # Those endpoints handle legacy event ids on their own so we ignore them here.
    _non_standard_id_endpoints = {'events.shorturl', 'events.display', 'events.display_overview'}

    @app.before_request
    def _redirect_legacy_id():
        if not request.view_args or request.endpoint in _non_standard_id_endpoints:
            return

        key = event_id = None
        if 'confId' in request.view_args:
            key = 'confId'
            event_id = request.view_args['confId']
        elif 'event_id' in request.view_args:
            key = 'event_id'
            event_id = request.view_args['event_id']

        if event_id is None or not is_legacy_id(event_id):
            return
        if request.method != 'GET':
            raise BadRequest('Unexpected non-GET request with legacy event ID')

        mapping = LegacyEventMapping.find_first(legacy_event_id=event_id)
        if mapping is None:
            raise NotFound('Legacy event {} does not exist'.format(event_id))

        request.view_args[key] = unicode(mapping.event_id)
        return redirect(url_for(request.endpoint, **dict(request.args.to_dict(), **request.view_args)), 301)


@signals.app_created.connect
def _check_roles(app, **kwargs):
    check_roles(Event)


@signals.acl.get_management_roles.connect_via(Event)
def _get_management_roles(sender, **kwargs):
    return SubmitterRole


class SubmitterRole(ManagementRole):
    name = 'submit'
    friendly_name = _('Submission')
    description = _('Grants access to materials and minutes.')


@signals.menu.items.connect_via('admin-sidemenu')
def _sidemenu_items(sender, **kwargs):
    if session.user.is_admin:
        yield SideMenuItem('reference_types', _('External ID Types'), url_for('events.reference_types'),
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

    yield MenuEntryData(_("Overview"), 'overview', 'events.display_overview', position=0, static_site=True)
    yield MenuEntryData(_("My Conference"), 'my_conference', position=7, visible=_my_conference_visible)


@signals.app_created.connect
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


@signals.event.cloned.connect
def _event_cloned(old_event, new_event, **kwargs):
    new_event.cloned_from = old_event
    new_event.keywords = old_event.keywords
    new_event.organizer_info = old_event.organizer_info
    new_event.additional_info = old_event.additional_info
    new_event.contact_title = old_event.contact_title
    new_event.contact_emails = old_event.contact_emails
    new_event.contact_phones = old_event.contact_phones


@template_hook('event-ical-export')
def _render_event_ical_export(event, **kwargs):
    from indico.modules.events.util import get_base_ical_parameters
    return render_template('events/display/event_ical_export.html', item=event,
                           ics_url=url_for('events.export_event_ical', event),
                           **get_base_ical_parameters(session.user, 'events', '/export/event/{0}.ics'.format(event.id)))

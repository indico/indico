# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json
import os
import random
import re
import warnings
from collections import defaultdict
from contextlib import contextmanager
from copy import deepcopy
from io import BytesIO
from mimetypes import guess_extension
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit
from zipfile import ZipFile

from flask import current_app, flash, g, redirect, request, session
from sqlalchemy import inspect
from sqlalchemy.orm import load_only, noload
from werkzeug.exceptions import BadRequest, Forbidden

from indico.core import signals
from indico.core.config import config
from indico.core.errors import NoReportError, UserValueError
from indico.core.permissions import FULL_ACCESS_PERMISSION, READ_ACCESS_PERMISSION
from indico.modules.categories.models.roles import CategoryRole
from indico.modules.events import Event
from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.modules.events.contributions import contribution_settings
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.layout import theme_settings
from indico.modules.events.models.events import EventType
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.models.principals import EventPrincipal
from indico.modules.events.models.roles import EventRole
from indico.modules.events.models.settings import EventSetting
from indico.modules.events.models.static_list_links import StaticListLink
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.timetable.models.breaks import Break
from indico.modules.events.timetable.models.entries import TimetableEntry
from indico.modules.networks import IPNetworkGroup
from indico.modules.users import User
from indico.util.caching import memoize_request
from indico.util.fs import chmod_umask, secure_filename
from indico.util.i18n import _
from indico.util.iterables import materialize_iterable
from indico.util.string import strip_tags
from indico.util.user import principal_from_identifier
from indico.web.flask.util import send_file, url_for
from indico.web.forms.colors import get_colors


def check_event_locked(rh, event, force=False):
    if (not getattr(rh, 'ALLOW_LOCKED', False) or force) and event.is_locked and request.method not in ('GET', 'HEAD'):
        raise NoReportError.wrap_exc(Forbidden(_('This event has been locked so no modifications are possible.')))


def get_object_from_args(args=None):
    """Retrieve an event object from request arguments.

    This utility is meant to be used in cases where the same controller
    can deal with objects attached to various parts of an event which
    use different URLs to indicate which object to use.

    :param args: The request arguments. If unspecified,
                 ``request.view_args`` is used.
    :return: An ``(object_type, event, object)`` tuple.  The event is
             always the :class:`Event` associated with the object.
             The object may be an `Event`, `Session`, `SessionBlock`, `Contribution`
             or `SubContribution`.  If the object does not exist,
             ``(object_type, None, None)`` is returned.
    """
    if args is None:
        args = request.view_args
    object_type = args['object_type']
    event = Event.get(args['event_id'], is_deleted=False)
    if event is None:
        obj = None
    elif object_type == 'event':
        obj = event
    elif object_type == 'session':
        obj = Session.query.with_parent(event).filter_by(id=args['session_id']).first()
    elif object_type == 'session_block':
        obj = (SessionBlock.query
               .filter(SessionBlock.id == args['session_block_id'],
                       SessionBlock.session.has(event=event, id=args['session_id'], is_deleted=False))
               .first())
    elif object_type == 'contribution':
        obj = Contribution.query.with_parent(event).filter_by(id=args['contrib_id']).first()
    elif object_type == 'subcontribution':
        obj = (SubContribution.query
               .filter(SubContribution.id == args['subcontrib_id'],
                       ~SubContribution.is_deleted,
                       SubContribution.contribution.has(event=event, id=args['contrib_id'], is_deleted=False))
               .first())
    elif object_type == 'abstract':
        obj = Abstract.query.with_parent(event).filter_by(id=args['abstract_id']).first()
    else:
        raise ValueError(f'Unexpected object type: {object_type}')
    if obj is not None:
        return object_type, event, obj
    else:
        return object_type, None, None


def get_theme(event, override_theme_id=None):
    """Get the theme ID and whether it's an override.

    This is useful for places where a user may specify a different
    timetable theme.  If the override theme is not valid for the
    event, a message is flashed and an exception redirecting the user
    to the main event page is raised.

    :raise BadRequest: if the override theme id is not valid
    :return: a ``(theme_id, is_override)`` tuple
    """
    if not override_theme_id:
        return event.theme, False
    elif override_theme_id == 'default':
        theme = theme_settings.defaults[event.type]
        return theme, theme != event.theme
    elif override_theme_id in theme_settings.get_themes_for(event.type_.name):
        return override_theme_id, override_theme_id != event.theme
    else:
        if override_theme_id in theme_settings.themes:
            flash(_("The theme '{}' is not valid for this event.").format(override_theme_id))
        else:
            flash(_("The theme '{}' does not exist.").format(override_theme_id))
        raise BadRequest(response=redirect(event.url))


def get_events_managed_by(user, dt=None):
    """Get the IDs of events where the user has management privs.

    :param user: A `User`
    :param dt: Only include events taking place on/after that date
    :return: A set of event ids
    """
    query = (user.in_event_acls
             .join(Event)
             .options(noload('user'), noload('local_group'), load_only('event_id'))
             .filter(~Event.is_deleted, Event.ends_after(dt))
             .filter(EventPrincipal.has_management_permission('ANY')))
    return {principal.event_id for principal in query}


def get_events_created_by(user, dt=None):
    """Get the IDs of events created by the user.

    :param user: A `User`
    :param dt: Only include events taking place on/after that date
    :return: A set of event ids
    """
    query = (user.created_events
             .filter(~Event.is_deleted, Event.ends_after(dt))
             .options(load_only('id')))
    return {event.id for event in query}


def get_events_with_linked_event_persons(user, dt=None):
    """
    Return a dict containing the event ids and role for all events
    where the user is a chairperson or (in case of a lecture) speaker.

    :param user: A `User`
    :param dt: Only include events taking place on/after that date
    """
    query = (user.event_persons
             .with_entities(EventPerson.event_id, Event._type)
             .join(Event, Event.id == EventPerson.event_id)
             .filter(EventPerson.event_links.any())
             .filter(~Event.is_deleted, Event.ends_after(dt)))
    return {event_id: ('lecture_speaker' if event_type == EventType.lecture else 'conference_chair')
            for event_id, event_type in query}


def get_random_color(event):
    breaks = Break.query.filter(Break.timetable_entry.has(event=event))
    used_colors = {s.colors for s in event.sessions} | {b.colors for b in breaks}
    unused_colors = set(get_colors()) - used_colors
    return random.choice(tuple(unused_colors) or get_colors())


def update_object_principals(obj, new_principals, read_access=False, full_access=False, permission=None):
    """Update an object's ACL with a new list of principals.

    Exactly one argument out of `read_access`, `full_access` and `role` must be specified.

    :param obj: The object to update. Must have ``acl_entries``
    :param new_principals: The set containing the new principals
    :param read_access: Whether the read access ACL should be updated
    :param full_access: Whether the full access ACL should be updated
    :param permission: The role ACL that should be updated
    """
    if read_access + full_access + bool(permission) != 1:
        raise ValueError('Only one ACL property can be specified')
    if full_access:
        existing = {acl.principal for acl in obj.acl_entries if acl.full_access}
        grant = {'full_access': True}
        revoke = {'full_access': False}
    elif read_access:
        existing = {acl.principal for acl in obj.acl_entries if acl.read_access}
        grant = {'read_access': True}
        revoke = {'read_access': False}
    elif permission:
        existing = {acl.principal
                    for acl in obj.acl_entries
                    if acl.has_management_permission(permission, explicit=True)}
        grant = {'add_permissions': {permission}}
        revoke = {'del_permissions': {permission}}

    new_principals = set(new_principals)
    added = new_principals - existing
    removed = existing - new_principals
    for principal in added:
        obj.update_principal(principal, **grant)
    for principal in removed:
        obj.update_principal(principal, **revoke)
    return {'added': added, 'removed': removed}


class ListGeneratorBase:
    """Base class for classes performing actions on Indico object lists.

    :param event: The associated `Event`
    :param entry_parent: The parent of the entries of the list. If it's None,
                         the parent is assumed to be the event itself.
    """

    #: The endpoint of the list management page
    endpoint = None
    #: Unique list identifier
    list_link_type = None
    #: The default list configuration dictionary
    default_list_config = None

    def __init__(self, event, entry_parent=None):
        #: The event the list is associated with
        self.event = event
        #: The parent object of the list items
        self.entry_parent = entry_parent or event
        #: Columns that originate from the list item's properties,
        #: relationships etc, but not from user defined fields (e.g.
        #: registration/contribution fields)
        self.static_items = {}
        self.extra_filters = {}
        self.static_link_used = 'config' in request.args

    def _get_config_session_key(self):
        """Compose the unique configuration ID.

        This ID will be used as a key to set the list's configuration to the
        session.
        """
        return f'{self.list_link_type}_config_{self.entry_parent.id}'

    def _get_config(self):
        """Load the list's configuration from the DB and return it."""
        session_key = self._get_config_session_key()
        if self.static_link_used:
            uuid = request.args['config']
            configuration = StaticListLink.load(self.event, self.list_link_type, uuid)
            if configuration and configuration['entry_parent_id'] == self.entry_parent.id:
                session[session_key] = configuration['data']
        return session.get(session_key, self.default_list_config)

    def _split_item_ids(self, item_ids, separator_type=None):
        """Separate the dynamic item ids from the static.

        :param item_ids: The list of ids to be splitted.
        :param separator_type: The type of the item to base the partitioning on.
                               If the value is 'dynamic', the function will
                               return a tuple where the first element is a list
                               of the dynamic item IDs and the second element a
                               list of the rest item IDs. If the value is
                               'static', the first element of the returned
                               tuple will be a list of the static item IDs.
        :return: A tuple of 2 lists as a result of the item_ids list
                 partitioning.
        """
        if separator_type == 'dynamic':
            dynamic_item_ids = [item_id for item_id in item_ids if not isinstance(item_id, str)]
            return dynamic_item_ids, [item_id for item_id in item_ids if item_id not in dynamic_item_ids]
        elif separator_type == 'static':
            static_item_ids = [item_id for item_id in item_ids if item_id in self.static_items]
            return static_item_ids, [item_id for item_id in item_ids if item_id not in static_item_ids]
        else:
            raise ValueError('Invalid separator_type')

    def _build_query(self):
        """Return the query of the list's entries.

        The query should not take into account the user's filtering
        configuration, for example::

            return Contribution.query.with_parent(self.event)
        """
        raise NotImplementedError

    def _filter_list_entries(self, query, filters):
        """Apply user's filters to query and return it."""
        raise NotImplementedError

    def _get_filters_from_request(self):
        """Get the new filters after the filter form is submitted."""
        def get_selected_options(item_id, item):
            if item.get('filter_choices') or item.get('type') == 'bool':
                return [x if x != 'None' else None for x in request.form.getlist(f'field_{item_id}')]

        filters = deepcopy(self.default_list_config['filters'])
        for item_id, item in self.static_items.items():
            options = get_selected_options(item_id, item)
            if options:
                filters['items'][item_id] = options
        for item_id, item in self.extra_filters.items():
            options = get_selected_options(item_id, item)
            if options:
                filters['extra'][item_id] = options
        return filters

    def get_list_url(self, uuid=None, external=False):
        """Return the URL of the list management page."""
        return url_for(self.endpoint, self.entry_parent, config=uuid, _external=external)

    def generate_static_url(self):
        """Return a URL with a uuid referring to the list's configuration."""
        session_key = self._get_config_session_key()
        configuration = {
            'entry_parent_id': self.entry_parent.id,
            'data': session.get(session_key)
        }
        if configuration['data']:
            link = StaticListLink.create(self.event, self.list_link_type, configuration)
            return self.get_list_url(uuid=link.uuid, external=True)
        else:
            return self.get_list_url(external=True)

    def store_configuration(self):
        """Load the filters from the request and store them in the session."""
        filters = self._get_filters_from_request()
        session_key = self._get_config_session_key()
        self.list_config = session.setdefault(session_key, {})
        self.list_config['filters'] = filters
        if request.values.get('visible_items'):
            visible_items = json.loads(request.values['visible_items'])
            self.list_config['items'] = sorted(visible_items, key=str)
        session.modified = True

    def flash_info_message(self, obj):
        raise NotImplementedError


def create_event_logo_tmp_file(event, tmpdir=None):
    """Create a temporary file with the event's logo.

    If `tmpdir` is specified, the logo file is created in there and
    a path relative to that directory is returned.
    """
    logo_meta = event.logo_metadata
    logo_extension = guess_extension(logo_meta['content_type']) or os.path.splitext(logo_meta['filename'])[1]
    with NamedTemporaryFile(delete=False, dir=(tmpdir or config.TEMP_DIR), suffix=logo_extension) as temp_file:
        temp_file.write(event.logo)
        temp_file.flush()
    return os.path.relpath(temp_file.name, tmpdir) if tmpdir else temp_file.name


@contextmanager
def track_time_changes(auto_extend=False, user=None):
    """Track time changes of event objects.

    This provides a list of changes while the context manager was
    active and also triggers `times_changed` signals.

    If the code running inside the ``with`` block of this context
    manager raises an exception, no signals will be triggered.

    :param auto_extend: Whether entry parents will get their boundaries
                        automatically extended or not. Passing ``'start'`` will
                        extend only start datetime, ``'end'`` to extend only
                        end datetime.
    :param user: The `User` that will trigger time changes.
    """
    if auto_extend:
        assert user is not None
    if 'old_times' in g:
        raise RuntimeError('time change tracking may not be nested')
    g.old_times = defaultdict(dict)
    changes = defaultdict(dict)
    try:
        yield changes
    except Exception:
        del g.old_times
        raise
    else:
        if auto_extend:
            by_start = auto_extend in (True, 'start')
            by_end = auto_extend in (True, 'end')
            initial_changes = set(g.old_times)
            # g.old_times changes during iteration
            for obj in list(g.old_times):
                if not isinstance(obj, Event):
                    obj.extend_parent(by_start=by_start, by_end=by_end)
            cascade_changes = set(g.old_times) - initial_changes
            for obj in cascade_changes:
                if isinstance(obj, Event):
                    if not obj.can_manage(user):
                        # TODO: raise Forbidden exceptions after adding protection check in the UI
                        raise UserValueError(_('Your action requires modification of event boundaries, but you are '
                                               'not authorized to manage the event.'))
                elif not obj.object.can_manage(user):
                    # TODO: raise Forbidden exceptions after adding protection check in the UI
                    raise UserValueError(_('Your action requires modification of session block boundaries, but you are '
                                           'not authorized to manage the session block.'))
        old_times = g.pop('old_times')
        for obj, info in old_times.items():
            if isinstance(obj, TimetableEntry):
                obj = obj.object
            if obj.start_dt != info['start_dt']:
                changes[obj]['start_dt'] = (info['start_dt'], obj.start_dt)
            if obj.duration != info['duration']:
                changes[obj]['duration'] = (info['duration'], obj.duration)
            if obj.end_dt != info['end_dt']:
                changes[obj]['end_dt'] = (info['end_dt'], obj.end_dt)
        for obj, obj_changes in changes.items():
            entry = None if isinstance(obj, Event) else obj.timetable_entry
            signals.event.times_changed.send(type(obj), entry=entry, obj=obj, changes=obj_changes)


def register_time_change(entry):
    """Register a time-related change for a timetable entry.

    This is an internal helper function used in the models to record
    changes of the start time or duration.  The changes are exposed
    through the `track_time_changes` contextmanager function.
    """
    # if it's a new object it's not a change so we just ignore it
    if not inspect(entry).persistent:
        return
    try:
        old_times = g.old_times
    except AttributeError:
        msg = f'Time change of {entry} was not tracked'
        if current_app.config.get('REPL'):
            warnings.warn(msg + ' (exception converted to a warning since you are using the REPL)', stacklevel=2)
            return
        elif current_app.config['TESTING']:
            warnings.warn(msg + ' (exception converted to a warning during tests)', stacklevel=2)
            return
        else:
            raise RuntimeError(msg)
    for field in ('start_dt', 'duration', 'end_dt'):
        if old_times[entry].get(field) is None:
            old_times[entry][field] = getattr(entry, field)


def register_event_time_change(event):
    """Register a time-related change for an event.

    This is an internal helper function used in the model to record
    changes of the start time or end time.  The changes are exposed
    through the `track_time_changes` contextmanager function.
    """
    # if it's a new object it's not a change so we just ignore it
    if not inspect(event).persistent:
        return
    try:
        old_times = g.old_times
    except AttributeError:
        msg = f'Time change of {event} was not tracked'
        if current_app.config.get('REPL'):
            warnings.warn(msg + ' (exception converted to a warning since you are using the REPL)', stacklevel=2)
            return
        elif current_app.config['TESTING']:
            warnings.warn(msg + ' (exception converted to a warning during tests)', stacklevel=2)
            return
        else:
            raise RuntimeError(msg)
    for field in ('start_dt', 'duration', 'end_dt'):
        if old_times[event].get(field) is None:
            old_times[event][field] = getattr(event, field)


@contextmanager
def track_location_changes():
    """Track location changes of event objects.

    This provides a list of changes while the context manager was
    active and also triggers `location_changed` signals.

    If the code running inside the ``with`` block of this context
    manager raises an exception, no signals will be triggered.
    """
    if 'old_locations' in g:
        raise RuntimeError('location change tracking may not be nested')
    g.old_locations = defaultdict(dict)
    changes = defaultdict(dict)
    try:
        yield changes
    except Exception:
        del g.old_locations
        raise
    else:
        old_locations = g.pop('old_locations')
        cols = ('own_room_id', 'own_room_name', 'own_venue_id', 'own_venue_name', 'own_address', 'inherit_location')
        for obj, info in old_locations.items():
            for col in cols:
                new_value = getattr(obj, col)
                if new_value != info[col]:
                    changes[obj][col] = (info[col], new_value)
        for obj, obj_changes in changes.items():
            signals.event.location_changed.send(type(obj), obj=obj, changes=obj_changes)


def register_location_change(entry):
    """Register a location-related change for an event object.

    This is an internal helper function used in the models to record
    changes of the location information.  The changes are exposed
    through the `track_location_changes` contextmanager function.
    """
    # if it's a new object it's not a change so we just ignore it
    if not inspect(entry).persistent:
        return
    try:
        old_locations = g.old_locations
    except AttributeError:
        msg = f'Location change of {entry} was not tracked'
        if current_app.config.get('REPL'):
            warnings.warn(msg + ' (exception converted to a warning since you are using the REPL)', stacklevel=2)
            return
        elif current_app.config['TESTING']:
            warnings.warn(msg + ' (exception converted to a warning during tests)', stacklevel=2)
            return
        else:
            raise RuntimeError(msg)
    for field in ('own_room_id', 'own_room_name', 'own_venue_id', 'own_venue_name', 'own_address', 'inherit_location'):
        if old_locations[entry].get(field) is None:
            old_locations[entry][field] = getattr(entry, field)


def serialize_event_for_ical(event):
    return {
        '_fossil': 'conferenceMetadata',
        'id': event.id,
        'title': event.title,
        'description': event.description,
        'startDate': event.start_dt,
        'endDate': event.end_dt,
        'url': event.external_url,
        'location': event.venue_name,
        'roomFullname': event.room_name,
        'speakers': [],
        'contributions': []
    }


def serialize_event_for_json_ld(event, full=False):
    data = {
        '@context': 'http://schema.org',
        '@type': 'Event',
        'url': event.external_url,
        'name': event.title,
        'startDate': event.start_dt_local.isoformat(),
        'endDate': event.end_dt_local.isoformat(),
        'location': {
            '@type': 'Place',
            'name': event.venue_name or 'No location set',
            'address': event.address or 'No address set'
        }
    }
    if full and event.default_locale:
        data['inLanguage'] = event.default_locale.replace('_', '-')
    if full and event.description:
        data['description'] = strip_tags(event.description)
    if full and event.person_links:
        data['performer'] = list(map(serialize_person_for_json_ld, event.person_links))
    if full and event.has_logo:
        data['image'] = event.external_logo_url
    return data


@materialize_iterable()
def serialize_events_for_json_ld(events, *, full=False):
    # We have to query the default locale separately because there's no way to
    # lazy-load them using the SettingsProxy, and when generating e.g. a category
    # listing we really don't want to spam an extra query for each event.
    query = (EventSetting.query
             .filter_by(module='language', name='default_locale')
             .filter(EventSetting.event_id.in_(e.id for e in events)))
    default_locales = {x.event: x.value for x in query}
    for event in events:
        data = serialize_event_for_json_ld(event, full=full)
        if locale := default_locales.get(event):
            data['inLanguage'] = locale.replace('_', '-')
        yield data


def serialize_person_for_json_ld(person):
    return {
        '@type': 'Person',
        'name': person.full_name,
        'affiliation': {
            '@type': 'Organization',
            'name': person.affiliation
        }
    }


def get_field_values(form_data):
    """Split the form fields between custom and static."""
    fields = {x: form_data[x] for x in form_data if not x.startswith('custom_')}
    custom_fields = {x: form_data[x] for x in form_data if x.startswith('custom_')}
    return fields, custom_fields


def set_custom_fields(obj, custom_fields_data):
    changes = {}
    for custom_field_name, custom_field_value in custom_fields_data.items():
        custom_field_id = int(custom_field_name[7:])  # Remove the 'custom_' part
        old_value = obj.set_custom_field(custom_field_id, custom_field_value)
        if old_value != custom_field_value:
            changes[custom_field_name] = (old_value, custom_field_value)
    return changes


def check_permissions(event, field, allow_networks=False):
    for principal_fossil, permissions in field.data:
        principal = principal_from_identifier(principal_fossil['identifier'],
                                              allow_external_users=True,
                                              allow_groups=True,
                                              allow_category_roles=True,
                                              allow_event_roles=True,
                                              allow_emails=True,
                                              allow_registration_forms=True,
                                              allow_networks=allow_networks,
                                              event_id=event.id)
        if isinstance(principal, IPNetworkGroup) and set(permissions) - {READ_ACCESS_PERMISSION}:
            return _('IP networks cannot have management permissions: {}').format(principal.name)
        if isinstance(principal, RegistrationForm) and set(permissions) - {READ_ACCESS_PERMISSION}:
            return _('Registrants cannot have management permissions: {}').format(principal.name)
        if FULL_ACCESS_PERMISSION in permissions and len(permissions) != 1:
            # when full access permission is set, discard rest of permissions
            permissions[:] = [FULL_ACCESS_PERMISSION]


def get_event_from_url(url):
    """Get an event from an Indico event URL."""
    data = urlsplit(url)
    if not all([data.scheme, data.netloc, data.path]):
        raise ValueError(_('Invalid event URL'))
    event_path = re.match(r'/event/(\d+)(/|$)', data.path)
    if not event_path:
        raise ValueError(_('Invalid event URL'))
    if not url.startswith(config.BASE_URL):
        raise ValueError(_('Events from other Indico instances cannot be imported'))
    event_id = event_path.group(1)
    event = Event.get(event_id, is_deleted=False)
    if not event:
        raise ValueError(_('This event does not exist'))
    return event


class ZipGeneratorMixin:
    """Mixin for RHs that generate zip with files."""

    def _adjust_path_length(self, segments):
        """Shorten the path length to < 260 chars.

        Windows' built-in ZIP tool doesn't like files whose
        total path exceeds ~260 chars. Here we progressively
        shorten the total until it matches that constraint.
        """
        result = []
        total_len = sum(len(seg) for seg in segments) + len(segments) - 1
        excess = (total_len - 255) if total_len > 255 else 0

        for seg in reversed(segments):
            fname, ext = os.path.splitext(seg)
            cut = min(excess, (len(fname) - 10) if len(fname) > 14 else 0)
            if cut:
                excess -= cut
                fname = fname[:-cut]
            result.append(fname + ext)

        return reversed(result)

    def _iter_items(self, files_holder):
        yield from files_holder

    def _get_item_path(self, item):
        return item.get_local_path()

    def _generate_zip_file(self, files_holder, name_prefix='material', name_suffix=None, return_file=False):
        """Generate a zip file containing the files passed.

        :param files_holder: An iterable (or an iterable containing) object that
                             contains the files to be added in the zip file.
        :param name_prefix: The prefix to the zip file name
        :param name_suffix: The suffix to the zip file name
        :param return_file: Return the temp file instead of a response
        """
        temp_file = NamedTemporaryFile(suffix='.zip', dir=config.TEMP_DIR, delete=False)  # noqa: SIM115
        with ZipFile(temp_file.name, 'w', allowZip64=True) as zip_handler:
            self.used_filenames = set()
            for item in self._iter_items(files_holder):
                name = self._prepare_folder_structure(item)
                self.used_filenames.add(name)
                with self._get_item_path(item) as filepath:
                    if isinstance(filepath, BytesIO):
                        zip_handler.writestr(name, filepath.getvalue())
                    else:
                        zip_handler.write(filepath, name)

        zip_file_name = f'{name_prefix}-{name_suffix}.zip' if name_suffix else f'{name_prefix}.zip'
        chmod_umask(temp_file.name)
        if return_file:
            return temp_file
        return send_file(zip_file_name, temp_file.name, 'application/zip', inline=False)

    def _prepare_folder_structure(self, item):
        file_name = secure_filename(f'{item.id}_{item.filename}', str(item.id))
        return os.path.join(*self._adjust_path_length([file_name]))


@memoize_request
def get_all_user_roles(event, user):
    event_roles = set(
        EventRole.query.with_parent(event)
        .filter(EventRole.members.any(User.id == user.id))
    )
    category_roles = set(
        CategoryRole.query
        .join(event.category.chain_query.subquery())
        .filter(CategoryRole.members.any(User.id == user.id))
    )
    return event_roles, category_roles


def should_show_draft_warning(event):
    return (event.type_ == EventType.conference and
            not contribution_settings.get(event, 'published') and
            (TimetableEntry.query.with_parent(event).has_rows() or
             Contribution.query.with_parent(event).has_rows()))


def format_log_ref(ref):
    return f'{ref.reference_type.name}:{ref.value}'


def _get_venue_room_name(data):
    venue_name = data['venue'].name if data.get('venue') else data.get('venue_name', '')
    room_name = data['room'].full_name if data.get('room') else data.get('room_name', '')
    return venue_name, room_name


def _format_location(data):
    venue_name = data[0]
    room_name = data[1]
    if venue_name and room_name:
        return f'{venue_name}: {room_name}'
    elif venue_name or room_name:
        return venue_name or room_name
    else:
        return None


def split_log_location_changes(changes):
    location_changes = changes.pop('location_data', None)
    if location_changes is None:
        return
    if location_changes[0]['address'] != location_changes[1]['address']:
        changes['address'] = (location_changes[0]['address'], location_changes[1]['address'])
    venue_room_changes = (_get_venue_room_name(location_changes[0]), _get_venue_room_name(location_changes[1]))
    if venue_room_changes[0] != venue_room_changes[1]:
        changes['venue_room'] = list(map(_format_location, venue_room_changes))


def format_log_person(data):
    return f'{data.full_name} <{data.email}>' if data.email else data.full_name

# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from flask import request, redirect, flash
from werkzeug.exceptions import BadRequest, NotFound

from indico.core import signals
from indico.core.db.sqlalchemy.principals import EmailPrincipal
from indico.core.roles import check_roles, ManagementRole
from indico.modules.events.models.events import Event
from indico.modules.events.models.legacy_mapping import LegacyEventMapping
from indico.modules.events.models.settings import EventSetting, EventSettingPrincipal
from indico.modules.events.util import notify_pending
from indico.web.flask.util import url_for
from indico.util.i18n import _, ngettext
from indico.util.string import is_legacy_id


#: URL prefixes for the various event objects (public area)
#: All prefixes are expected to be used inside the '/event/<confId>'
#: url space.
event_object_url_prefixes = {
    'event': [''],
    'session': ['/session/<sessionId>'],
    'contribution': ['/session/<sessionId>/contribution/<contribId>', '/contribution/<contribId>'],
    'subcontribution': ['/session/<sessionId>/contribution/<contribId>/<subContId>',
                        '/contribution/<contribId>/<subContId>']
}

#: URL prefixes for the various event objects (management area)
#: All prefixes are expected to be used inside the '/event/<confId>'
#: url space.
event_management_object_url_prefixes = {
    'event': ['/manage'],
    'session': ['/manage/session/<sessionId>'],
    'contribution': ['/manage/session/<sessionId>/contribution/<contribId>', '/manage/contribution/<contribId>'],
    'subcontribution': ['/manage/session/<sessionId>/contribution/<contribId>/subcontribution/<subContId>',
                        '/manage/contribution/<contribId>/subcontribution/<subContId>']
}


@signals.event.deleted.connect
def _event_deleted(event, **kwargs):
    event.as_event.is_deleted = True
    EventSetting.delete_event(int(event.id))
    EventSettingPrincipal.delete_event(int(event.id))
    if hasattr(event, '_old_id'):
        LegacyEventMapping.find(legacy_event_id=event._old_id).delete()


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    from indico.modules.events.models.principals import EventPrincipal
    EventPrincipal.merge_users(target, source, 'event_new')


@signals.users.registered.connect
@signals.users.email_added.connect
def _convert_email_principals(user, **kwargs):
    from indico.modules.events.models.principals import EventPrincipal
    events = EventPrincipal.replace_email_with_user(user, 'event_new')
    if events:
        num = len(events)
        flash(ngettext("You have been granted manager/submission privileges for an event.",
                       "You have been granted manager/submission privileges for {} events.", num).format(num), 'info')


@signals.acl.entry_changed.connect_via(Event)
def _notify_pending(sender, obj, principal, entry, is_new, **kwargs):
    if entry is None or not is_new or not isinstance(principal, EmailPrincipal):
        return
    notify_pending(entry)


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
    _shorturl_endpoints = {'event.shorturl', 'event.conferenceDisplay', 'conferenceDisplay-overview'}

    @app.before_request
    def _redirect_legacy_id():
        if not request.view_args or request.endpoint in _shorturl_endpoints:
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
def _check_roles(app, **kawrgs):
    check_roles(Event)


@signals.acl.get_management_roles.connect_via(Event)
def _get_management_roles(sender, **kwargs):
    return SubmitterRole


class SubmitterRole(ManagementRole):
    name = 'submit'
    friendly_name = _('Submission')
    description = _('Grants access to materials and minutes.')

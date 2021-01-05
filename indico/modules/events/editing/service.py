# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import requests
from marshmallow import ValidationError
from werkzeug.urls import url_parse

import indico
from indico.core.config import config
from indico.core.db import db
from indico.modules.events.editing import logger
from indico.modules.events.editing.models.editable import EditableType
from indico.modules.events.editing.models.revisions import FinalRevisionState
from indico.modules.events.editing.operations import create_revision_comment, publish_editable_revision
from indico.modules.events.editing.schemas import (EditableBasicSchema, EditingRevisionSignedSchema,
                                                   ServiceActionResultSchema, ServiceActionSchema,
                                                   ServiceReviewEditableSchema, ServiceUserSchema)
from indico.modules.events.editing.settings import editing_settings
from indico.modules.users import User
from indico.util.caching import memoize_redis
from indico.util.i18n import _
from indico.web.flask.util import url_for


class ServiceRequestFailed(Exception):
    def __init__(self, exc):
        error = None
        if isinstance(exc, requests.RequestException) and exc.response is not None:
            try:
                error = exc.response.json()['error']
            except (ValueError, KeyError):
                # not json or not error field
                error = None
        super(ServiceRequestFailed, self).__init__(error or unicode(exc))


@memoize_redis(30)
def check_service_url(url):
    try:
        resp = requests.get(url + '/info', allow_redirects=False)
        resp.raise_for_status()
        if resp.status_code != 200:
            raise requests.HTTPError('Unexpected status code: {}'.format(resp.status_code), response=resp)
        info = resp.json()
    except requests.ConnectionError as exc:
        return {'info': None, 'error': _('Connection failed')}
    except requests.RequestException as exc:
        return {'info': None, 'error': unicode(ServiceRequestFailed(exc))}
    if not all(x in info for x in ('name', 'version')):
        return {'error': _('Invalid response')}
    return {'error': None, 'info': info}


def _build_url(event, path):
    return editing_settings.get(event, 'service_url') + path


def _get_headers(event, include_token=True):
    headers = {'Accept': 'application/json',
               'User-Agent': 'Indico/{}'.format(indico.__version__)}
    if include_token:
        headers['Authorization'] = 'Bearer {}'.format(editing_settings.get(event, 'service_token'))
    return headers


def _log_service_error(exc, msg):
    payload = None
    if exc.response is not None:
        try:
            payload = exc.response.json()
        except ValueError:
            pass
    if payload is not None:
        logger.exception('{}: %s'.format(msg), payload)
    else:
        logger.exception(msg)


def make_event_identifier(event):
    data = url_parse(config.BASE_URL)
    parts = data.netloc.split('.')
    if data.path:
        parts += data.path.split('/')
    return '{}-{}'.format('-'.join(parts), event.id)


def _get_event_identifier(event):
    identifier = editing_settings.get(event, 'service_event_identifier')
    assert identifier
    return identifier


def service_handle_enabled(event):
    data = {
        'title': event.title,
        'url': event.external_url,
        'token': editing_settings.get(event, 'service_token'),
        'endpoints': _get_event_endpoints(event)
    }
    try:
        resp = requests.put(_build_url(event, '/event/{}'.format(_get_event_identifier(event))),
                            headers=_get_headers(event, include_token=False), json=data)
        resp.raise_for_status()
    except requests.RequestException as exc:
        _log_service_error(exc, 'Registering event with service failed')
        raise ServiceRequestFailed(exc)


def service_handle_disconnected(event):
    try:
        resp = requests.delete(_build_url(event, '/event/{}'.format(_get_event_identifier(event))),
                               headers=_get_headers(event))
        resp.raise_for_status()
    except requests.RequestException as exc:
        _log_service_error(exc, 'Disconnecting event from service failed')
        raise ServiceRequestFailed(exc)


def service_get_status(event):
    try:
        resp = requests.get(_build_url(event, '/event/{}'.format(_get_event_identifier(event))),
                            headers=_get_headers(event))
        resp.raise_for_status()
    except requests.ConnectionError as exc:
        return {'status': None, 'error': _('Connection failed')}
    except requests.RequestException as exc:
        return {'status': None, 'error': unicode(ServiceRequestFailed(exc))}
    return {'status': resp.json(), 'error': None}


def service_handle_new_editable(editable, user):
    revision = editable.revisions[-1]
    data = {
        'editable': EditableBasicSchema().dump(editable),
        'revision': EditingRevisionSignedSchema().dump(revision),
        'endpoints': _get_revision_endpoints(revision),
        'user': ServiceUserSchema(context={'editable': editable}).dump(user),
    }
    try:
        path = '/event/{}/editable/{}/{}'.format(
            _get_event_identifier(editable.event),
            editable.type.name,
            editable.contribution_id,
        )
        resp = requests.put(_build_url(editable.event, path), headers=_get_headers(editable.event), json=data)
        resp.raise_for_status()
    except requests.RequestException as exc:
        _log_service_error(exc, 'Calling listener for new editable failed')
        raise ServiceRequestFailed(exc)


def service_handle_review_editable(editable, user, action, parent_revision, revision=None):
    new_revision = revision or parent_revision
    data = {
        'action': action.name,
        'revision': EditingRevisionSignedSchema().dump(new_revision),
        'endpoints': _get_revision_endpoints(new_revision),
        'user': ServiceUserSchema(context={'editable': editable}).dump(user),
    }
    try:
        path = '/event/{}/editable/{}/{}/{}'.format(
            _get_event_identifier(editable.event),
            editable.type.name,
            editable.contribution_id,
            new_revision.id
        )
        resp = requests.post(_build_url(editable.event, path), headers=_get_headers(editable.event),
                             json=data)
        resp.raise_for_status()
        resp = ServiceReviewEditableSchema().load(resp.json())

        if 'comment' in resp:
            parent_revision.comment = resp['comment']
        if 'tags' in resp:
            parent_revision.tags = {tag for tag in editable.event.editing_tags
                                    if tag.id in map(int, resp['tags'])}
        for comment in resp.get('comments', []):
            create_revision_comment(new_revision, User.get_system_user(), comment['text'], internal=comment['internal'])

        db.session.flush()
        return resp
    except (requests.RequestException, ValidationError) as exc:
        _log_service_error(exc, 'Calling listener for editable revision failed')
        raise ServiceRequestFailed(exc)


def service_get_custom_actions(editable, revision, user):
    data = {
        'revision': EditingRevisionSignedSchema().dump(revision),
        'user': ServiceUserSchema(context={'editable': editable}).dump(user),
    }

    path = '/event/{}/editable/{}/{}/{}/actions'.format(
        _get_event_identifier(editable.event),
        editable.type.name,
        editable.contribution_id,
        revision.id
    )
    try:
        resp = requests.post(_build_url(editable.event, path), headers=_get_headers(editable.event), json=data)
        resp.raise_for_status()
        return ServiceActionSchema(many=True).load(resp.json())
    except (requests.RequestException, ValidationError) as exc:
        _log_service_error(exc, 'Calling listener for custom actions failed')
        raise ServiceRequestFailed(exc)


def service_handle_custom_action(editable, revision, user, action):
    data = {
        'action': action,
        'revision': EditingRevisionSignedSchema().dump(revision),
        'endpoints': _get_revision_endpoints(revision),
        'user': ServiceUserSchema(context={'editable': editable}).dump(user),
    }
    try:
        path = '/event/{}/editable/{}/{}/{}/action'.format(
            _get_event_identifier(editable.event),
            editable.type.name,
            editable.contribution_id,
            revision.id
        )
        resp = requests.post(_build_url(editable.event, path), headers=_get_headers(editable.event), json=data)
        resp.raise_for_status()
        resp = ServiceActionResultSchema().load(resp.json())
    except (requests.RequestException, ValidationError) as exc:
        _log_service_error(exc, 'Calling listener for triggering custom action failed')
        raise ServiceRequestFailed(exc)

    if revision.final_state == FinalRevisionState.accepted:
        publish = resp.get('publish')
        if publish:
            publish_editable_revision(revision)
        elif publish is False:
            revision.editable.published_revision = None
    if 'tags' in resp:
        revision.tags = {tag for tag in editable.event.editing_tags if tag.id in map(int, resp['tags'])}
    for comment in resp.get('comments', []):
        create_revision_comment(revision, User.get_system_user(), comment['text'], internal=comment['internal'])
    db.session.flush()
    return resp


def _get_event_endpoints(event):
    return {
        'tags': {
            'create': url_for('.api_create_tag', event, _external=True),
            'list': url_for('.api_tags', event, _external=True)
        },
        'editable_types': url_for('.api_enabled_editable_types', event, _external=True),
        'file_types': {
            t.name: {
                'create': url_for('.api_add_file_type', event, type=t.name, _external=True),
                'list': url_for('.api_file_types', event, type=t.name, _external=True),
            } for t in EditableType
        }
    }


def _get_revision_endpoints(revision):
    return {
        'revisions': {
            'details': url_for('.api_editable', revision, _external=True),
            'replace': url_for('.api_replace_revision', revision, _external=True),
            'undo': url_for('.api_undo_review', revision, _external=True)
        },
        'file_upload': url_for('.api_upload', revision, _external=True)
    }

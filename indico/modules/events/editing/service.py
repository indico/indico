# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import requests
from werkzeug.urls import url_parse

import indico
from indico.core.config import config
from indico.modules.events.editing import logger
from indico.modules.events.editing.models.editable import EditableType
from indico.modules.events.editing.settings import editing_settings
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
        'config_endpoints': {
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
    }
    try:
        resp = requests.put(_build_url(event, '/event/{}'.format(_get_event_identifier(event))),
                            headers=_get_headers(event, include_token=False), json=data)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.exception('Registering event with service failed')
        raise ServiceRequestFailed(exc)


def service_handle_disconnected(event):
    try:
        resp = requests.delete(_build_url(event, '/event/{}'.format(_get_event_identifier(event))),
                               headers=_get_headers(event))
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.exception('Disconnecting event from service failed')
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

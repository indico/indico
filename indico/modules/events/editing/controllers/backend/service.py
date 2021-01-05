# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from uuid import uuid4

from flask import jsonify
from webargs import fields
from webargs.flaskparser import abort
from werkzeug.exceptions import BadRequest, ServiceUnavailable

from indico.core.config import config
from indico.core.db import db
from indico.modules.events.editing.controllers.base import RHEditingManagementBase
from indico.modules.events.editing.service import (ServiceRequestFailed, check_service_url, make_event_identifier,
                                                   service_get_status, service_handle_disconnected,
                                                   service_handle_enabled)
from indico.modules.events.editing.settings import editing_settings
from indico.util.i18n import _
from indico.web.args import use_kwargs


class RHCheckServiceURL(RHEditingManagementBase):
    """Check the service URL provided by a user."""

    @use_kwargs({
        'url': fields.URL(schemes={'http', 'https'}, required=True),
    })
    def _process(self, url):
        url = url.rstrip('/')
        return jsonify(check_service_url(url))


class RHConnectService(RHEditingManagementBase):
    """Set the service URL to be used for the event's editing workflow."""

    @use_kwargs({
        'url': fields.URL(schemes={'http', 'https'}, required=True),
    })
    def _process(self, url):
        if not config.EXPERIMENTAL_EDITING_SERVICE:
            raise ServiceUnavailable('This functionality is not available yet')
        if editing_settings.get(self.event, 'service_url'):
            raise BadRequest('Service URL already set')
        url = url.rstrip('/')
        info = check_service_url(url)
        if info['error'] is not None:
            abort(422, messages={'url': [info['error']]})
        if not editing_settings.get(self.event, 'service_event_identifier'):
            editing_settings.set(self.event, 'service_event_identifier', make_event_identifier(self.event))
        editing_settings.set_multi(self.event, {
            'service_url': url,
            'service_token': unicode(uuid4()),
        })
        # we need to commit the token so the service can already use it when processing
        # the enabled event in case it wants to set up tags etc
        db.session.commit()
        try:
            service_handle_enabled(self.event)
        except ServiceRequestFailed as exc:
            editing_settings.delete(self.event, 'service_url', 'service_token')
            db.session.commit()
            raise ServiceUnavailable(_('Could not register event with service: {}').format(exc))
        except Exception:
            editing_settings.delete(self.event, 'service_url', 'service_token')
            db.session.commit()
            raise
        return '', 204


class RHDisconnectService(RHEditingManagementBase):
    """Disconnect the event from the editing workflow service."""

    @use_kwargs({
        'force': fields.Bool(missing=False),
    })
    def _process(self, force):
        if not editing_settings.get(self.event, 'service_url'):
            raise BadRequest('Service URL not set')
        status = service_get_status(self.event)
        notify_service = True
        if status['error']:
            if not force:
                # this only happens if the service went down between loading
                # the page and sending the disconnect request
                raise BadRequest('Cannot disconnect service')
            notify_service = False
        elif not status['status']['can_disconnect']:
            raise BadRequest('Cannot disconnect service')
        if notify_service:
            try:
                service_handle_disconnected(self.event)
            except ServiceRequestFailed as exc:
                raise ServiceUnavailable(_('Could not disconnect event from service: {}').format(exc))
        editing_settings.delete(self.event, 'service_url', 'service_token')
        return '', 204


class RHServiceStatus(RHEditingManagementBase):
    """Get the status of the currently connected service."""

    def _process(self):
        if not editing_settings.get(self.event, 'service_url'):
            return jsonify(connected=False, error=None, status=None)
        status = service_get_status(self.event)
        return jsonify(connected=True, error=status['error'], status=status['status'])

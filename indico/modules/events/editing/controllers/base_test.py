# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from uuid import uuid4

from indico.core.oauth.util import TOKEN_PREFIX_SERVICE
from indico.modules.events.editing.controllers.base import TokenAccessMixin
from indico.modules.events.editing.settings import editing_settings
from indico.web.flask.util import make_view_func
from indico.web.rh import RH


def test_token_access_mixin(dummy_event, app, test_client):
    class RHTest(TokenAccessMixin, RH):
        def _process(self):
            return f'{self._token_can_access()}|{self.is_service_call}'.lower()

    class RHTestServiceAllowed(TokenAccessMixin, RH):
        SERVICE_ALLOWED = True

        def can_access(self):
            # must be called here for CSRF
            self._token_can_access()

        def _process(self):
            return f'{self._token_can_access()}|{self.is_service_call}'.lower()

    app.add_url_rule('/test/<int:event_id>/no-service', 'test_no_service', make_view_func(RHTest))
    app.add_url_rule('/test/<int:event_id>/service', 'test_service', make_view_func(RHTestServiceAllowed),
                     methods=('GET', 'POST'))

    token = f'{TOKEN_PREFIX_SERVICE}{uuid4()}'
    editing_settings.set(dummy_event, 'service_token', token)

    # no auth
    assert test_client.get(f'/test/{dummy_event.id}/no-service').data == b'false|false'
    assert test_client.get(f'/test/{dummy_event.id}/service').data == b'false|false'
    # service token
    service_auth = {'headers': {'Authorization': f'Bearer {token}'}}
    assert test_client.get(f'/test/{dummy_event.id}/no-service', **service_auth).data == b'false|false'
    assert test_client.get(f'/test/{dummy_event.id}/service', **service_auth).data == b'true|true'
    # csrf
    resp = test_client.post(f'/test/{dummy_event.id}/service')
    assert resp.status_code == 400
    assert b'problem with your current session' in resp.data
    assert test_client.post(f'/test/{dummy_event.id}/service', **service_auth).data == b'true|true'

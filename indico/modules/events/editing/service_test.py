# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json
from pathlib import Path

import pytest
from itsdangerous import URLSafeSerializer

from indico.modules.events.editing.models.revisions import RevisionType
from indico.modules.events.editing.settings import editing_settings
from indico.testing.util import assert_yaml_snapshot


SNAPSHOT_DIR = Path(__file__).parent / 'tests'
MOCK_SVC = 'https://editingsvc.local'


@pytest.fixture(autouse=True)
def configure_editing_service(dummy_event):
    editing_settings.set_multi(dummy_event, {
        'service_url': MOCK_SVC,
        'service_event_identifier': 'dummy',
    })


@pytest.fixture(autouse=True)
def static_signature(mocker):
    """Ensure signed URLs do not change between test runs."""
    mocker.patch.object(URLSafeSerializer, 'dumps').return_value = 'signature'


def _assert_yaml_snapshot(snapshot, data, name):
    __tracebackhide__ = True
    snapshot.snapshot_dir = SNAPSHOT_DIR
    assert_yaml_snapshot(snapshot, data, name, strip_dynamic_data=True)


@pytest.mark.parametrize('set_ready_for_review', (False, True))
def test_service_handle_new_editable(dummy_editable, dummy_user, mocked_responses, snapshot, set_ready_for_review,
                                     dummy_editing_revision):
    from indico.modules.events.editing.service import service_handle_new_editable
    response_payload = {'ready_for_review': True} if set_ready_for_review else None
    resp = mocked_responses.put(f'{MOCK_SVC}/event/dummy/editable/paper/{dummy_editable.id}', json=response_payload)
    service_handle_new_editable(dummy_editable, dummy_user)
    req_payload = json.loads(resp.calls[0].request.body)
    _assert_yaml_snapshot(snapshot, req_payload, 'service_new_editable.yml')
    if set_ready_for_review:
        assert dummy_editing_revision.type == RevisionType.ready_for_review
    else:
        assert dummy_editing_revision.type != RevisionType.ready_for_review

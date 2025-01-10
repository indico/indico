# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json
from pathlib import Path
from unittest.mock import Mock

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


def test_service_handle_enabled(dummy_event, mocked_responses, snapshot):
    from indico.modules.events.editing.service import service_handle_enabled
    resp = mocked_responses.put(f'{MOCK_SVC}/event/dummy')
    service_handle_enabled(dummy_event)
    req_payload = json.loads(resp.calls[0].request.body)
    _assert_yaml_snapshot(snapshot, req_payload, 'service_enabled.yml')


def test_service_handle_disconnected(dummy_event, mocked_responses):
    from indico.modules.events.editing.service import service_handle_disconnected
    mocked_responses.delete(f'{MOCK_SVC}/event/dummy')
    service_handle_disconnected(dummy_event)


def test_service_get_status(dummy_event, mocked_responses):
    from indico.modules.events.editing.service import service_get_status
    mocked_responses.get(f'{MOCK_SVC}/event/dummy', json={})
    service_get_status(dummy_event)


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


def test_service_handle_review_editable(dummy_editable, dummy_user, dummy_editing_revision, mocked_responses, snapshot):
    from indico.modules.events.editing.schemas import EditingReviewAction
    from indico.modules.events.editing.service import service_handle_review_editable
    mock_parent_revision = Mock()
    resp = mocked_responses.post(f'{MOCK_SVC}/event/dummy/editable/paper/420/420', json={'comment': 'foobar'})
    service_handle_review_editable(dummy_editable, dummy_user, EditingReviewAction.accept, mock_parent_revision,
                                   dummy_editing_revision)
    req_payload = json.loads(resp.calls[0].request.body)
    _assert_yaml_snapshot(snapshot, req_payload, 'service_review_editable.yml')
    assert mock_parent_revision.comment == 'foobar'


def test_service_handle_delete_editable(dummy_editable, mocked_responses, snapshot):
    from indico.modules.events.editing.service import service_handle_delete_editable
    mocked_responses.delete(f'{MOCK_SVC}/event/dummy/editable/paper/420')
    service_handle_delete_editable(dummy_editable)


def test_service_get_custom_action(dummy_editable, dummy_editing_revision, dummy_user, mocked_responses, snapshot):
    from indico.modules.events.editing.service import service_get_custom_actions
    resp = mocked_responses.post(f'{MOCK_SVC}/event/dummy/editable/paper/420/420/actions', json={})
    service_get_custom_actions(dummy_editable, dummy_editing_revision, dummy_user)
    req_payload = json.loads(resp.calls[0].request.body)
    _assert_yaml_snapshot(snapshot, req_payload, 'service_get_custom_action.yml')


@pytest.mark.usefixtures('request_context', 'dummy_editing_tag')
def test_service_handle_custom_action(dummy_editable, dummy_editing_revision, dummy_user, mocked_responses, snapshot):
    from indico.modules.events.editing.service import service_handle_custom_action
    resp = mocked_responses.post(
        f'{MOCK_SVC}/event/dummy/editable/paper/420/420/action',
        json={
            'publish': True,
            'comments': [{'text': 'foobar'}],
            'tags': [420],
            'redirect': 'https://foo.bar',
            'reset': False
        }
    )
    assert not dummy_editing_revision.tags
    assert not dummy_editing_revision.comments
    rv = service_handle_custom_action(dummy_editable, dummy_editing_revision, dummy_user, 'foobar')
    req_payload = json.loads(resp.calls[0].request.body)
    _assert_yaml_snapshot(snapshot, req_payload, 'service_custom_action.yml')
    assert len(dummy_editing_revision.tags) == 1
    assert len(dummy_editing_revision.comments) == 1
    assert rv['redirect'] == 'https://foo.bar'

# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.models.series import EventSeries


@pytest.mark.usefixtures('no_csrf_check')
def test_series_api_unauthenticated(test_client, db):
    series = EventSeries()
    db.session.add(series)
    db.session.flush()
    resp = test_client.post('/event-series/', json={})
    assert resp.status_code == 403
    resp = test_client.get(f'/event-series/{series.id}', json={})  # fake json to avoid login page redirect
    assert resp.status_code == 403
    resp = test_client.patch(f'/event-series/{series.id}', json={})
    assert resp.status_code == 403
    resp = test_client.delete(f'/event-series/{series.id}', json={})
    assert resp.status_code == 403


@pytest.mark.usefixtures('no_csrf_check')
def test_series_api_not_manager(dummy_user, dummy_event, create_event, test_client, db):
    with test_client.session_transaction() as sess:
        sess.set_session_user(dummy_user)
    # create
    resp = test_client.post('/event-series/', json={'event_ids': [dummy_event.id]})
    assert resp.status_code == 422
    assert resp.json == {'webargs_errors': {'event_ids': ['You must be a manager of all chosen events.']}}

    series = EventSeries(events=[dummy_event])
    db.session.add(series)
    db.session.flush()

    # get
    resp = test_client.get(f'/event-series/{series.id}')
    assert resp.status_code == 403
    assert 'You can only manage a series if you can manage all its events.' in resp.text
    # modify
    resp = test_client.patch(f'/event-series/{series.id}', json={})
    assert resp.status_code == 403
    assert 'You can only manage a series if you can manage all its events.' in resp.text
    # delete
    resp = test_client.delete(f'/event-series/{series.id}', json={})
    assert resp.status_code == 403
    assert 'You can only manage a series if you can manage all its events.' in resp.text

    # do not allow adding an event not managed by the user
    dummy_event.update_principal(dummy_user, full_access=True)
    other_event = create_event()
    resp = test_client.patch(f'/event-series/{series.id}', json={'event_ids': [dummy_event.id, other_event.id]})
    assert resp.status_code == 422
    assert resp.json == {'webargs_errors': {'event_ids': ['You must be a manager of all chosen events.']}}


@pytest.mark.usefixtures('no_csrf_check')
def test_series_api(dummy_event, dummy_user, test_client):
    payload = {'event_ids': [dummy_event.id]}
    with test_client.session_transaction() as sess:
        sess.set_session_user(dummy_user)

    # successful creation
    dummy_event.update_principal(dummy_user, full_access=True)
    assert not EventSeries.query.has_rows()
    resp = test_client.post('/event-series/', json=payload)
    assert resp.status_code == 204
    series = EventSeries.query.one()

    resp = test_client.get(f'/event-series/{series.id}')
    assert resp.json == {
        'event_title_pattern': '',
        'events': [
            {
                'category_chain': dummy_event.category.chain_titles,
                'end_dt': dummy_event.end_dt.isoformat(),
                'id': dummy_event.id,
                'start_dt': dummy_event.start_dt.isoformat(),
                'title': dummy_event.title,
            },
        ],
        'id': series.id,
        'show_links': True,
        'show_sequence_in_title': True,
    }

    resp = test_client.patch(f'/event-series/{series.id}', json={'show_links': False})
    assert resp.status_code == 204
    assert not series.show_links

    resp = test_client.delete(f'/event-series/{series.id}')
    assert resp.status_code == 204
    assert not EventSeries.query.has_rows()

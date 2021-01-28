# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.models.legacy_mapping import LegacyEventMapping


@pytest.mark.parametrize('url', ('/event/{}/timetable/', '/event/{}/'))
def test_not_legacy(create_event, test_client, url):
    event = create_event()
    event.title = f'dummy#{event.id}'
    assert event.id != 0
    rv = test_client.get(url.format(event.id))
    assert f'dummy#{event.id}'.encode() in rv.data
    assert rv.status_code == 200


@pytest.mark.parametrize('url', ('/event/0/timetable/', '/event/0/'))
def test_not_legacy_id_0(dummy_event, test_client, url):
    # `0` could look legacy ("leading zero") but it's not
    assert dummy_event.id == 0
    rv = test_client.get(url)
    assert b'dummy#0' in rv.data
    assert rv.status_code == 200


@pytest.mark.usefixtures('db')
def test_legacy_id_not_mapped(test_client):
    # legacy id but not in the mapping table
    rv = test_client.get('event/0999/timetable/')
    assert b'Legacy event 0999 does not exist' in rv.data
    assert rv.status_code == 404

    rv = test_client.get('event/0999/')
    assert b'An event with this ID/shortcut does not exist.' in rv.data
    assert rv.status_code == 404


@pytest.mark.parametrize('url', ('/event/{}/timetable', '/event/{}/timetable/', '/event/{}/'))
@pytest.mark.parametrize('legacy_id', ('0123', 'a123', 'a0', 'asdf', '123x', '0xff'))
def test_legacy_ids(db, dummy_event, test_client, url, legacy_id):
    db.session.add(LegacyEventMapping(legacy_event_id=legacy_id, event=dummy_event))
    rv = test_client.get(url.format(legacy_id))
    assert rv.status_code == 301
    assert rv.headers['Location'] == 'http://localhost' + url.format(dummy_event.id)

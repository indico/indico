# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest


@pytest.mark.usefixtures('no_csrf_check')
def test_unlisted_event_publish_button_inside_alert(create_event, dummy_user, test_client):
    event = create_event(category=None)
    event.update_principal(dummy_user, full_access=True)
    with test_client.session_transaction() as sess:
        sess.set_session_user(dummy_user)
    resp = test_client.get(f'/event/{event.id}/manage/')
    assert resp.status_code == 200
    alert = resp.text.index('This event is currently unlisted')
    assert 'event-action-publish-container' not in resp.text[:alert]
    assert 'event-action-publish-container' in resp.text[alert:]

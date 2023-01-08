# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from flask import session

from indico.modules.categories.models.categories import EventCreationMode
from indico.modules.events.management.controllers.actions import RHMoveEvent


@pytest.fixture
def target_category(create_category):
    return create_category(25, title='Target')


@pytest.mark.parametrize(('creation_mode', 'permissions'), (
    (EventCreationMode.moderated, set()),
    (EventCreationMode.restricted, {'event_move_request'})
))
def test_move_event_request(db, app, creation_mode, permissions, dummy_user, dummy_event,
                            dummy_category, target_category):
    dummy_event.category = dummy_category
    dummy_event.update_principal(dummy_user, full_access=True)
    target_category.event_creation_mode = creation_mode
    target_category.update_principal(dummy_user, read_access=True, permissions=permissions)
    assert dummy_event.pending_move_request is None
    rh = RHMoveEvent()
    rh.comment = 'foo'
    rh.event = dummy_event
    rh.target_category = target_category
    with app.test_request_context():
        session.set_session_user(dummy_user)
        rh._check_access()
        rh._process()
        db.session.expire(dummy_event, ['pending_move_request'])
        assert dummy_event.category == dummy_category
        assert dummy_event.pending_move_request is not None
        assert dummy_event.pending_move_request.category == target_category
        assert dummy_event.pending_move_request.requestor_comment == rh.comment


def test_move_event(app, dummy_event, dummy_user, dummy_category, target_category):
    dummy_event.category = dummy_category
    dummy_event.update_principal(dummy_user, full_access=True)
    target_category.event_creation_mode = EventCreationMode.open
    target_category.update_principal(dummy_user, read_access=True, permissions={'create'})
    assert dummy_event.pending_move_request is None
    rh = RHMoveEvent()
    rh.comment = ''
    rh.event = dummy_event
    rh.target_category = target_category
    with app.test_request_context():
        session.set_session_user(dummy_user)
        rh._check_access()
        rh._process()
        assert dummy_event.category == target_category
        assert dummy_event.pending_move_request is None

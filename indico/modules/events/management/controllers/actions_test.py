import pytest

from indico.modules.events.management.controllers.actions import RHMoveEvent


@pytest.fixture
def target_category(create_category):
    return create_category(25, title='Target')


def test_move_event_request(app, dummy_event, dummy_category, target_category):
    dummy_event.category = dummy_category
    target_category.event_requires_approval = True
    assert dummy_event.pending_move_request is None
    rh = RHMoveEvent()
    rh.event = dummy_event
    rh.target_category = target_category
    with app.test_request_context():
        rh._process()
        assert dummy_event.category == dummy_category
        assert dummy_event.pending_move_request is not None
        assert dummy_event.pending_move_request.category == target_category


def test_move_event(app, dummy_event, dummy_category, target_category):
    dummy_event.category = dummy_category
    target_category.event_requires_approval = False
    assert dummy_event.pending_move_request is None
    rh = RHMoveEvent()
    rh.event = dummy_event
    rh.target_category = target_category
    with app.test_request_context():
        rh._process()
        assert dummy_event.category == target_category
        assert dummy_event.pending_move_request is None

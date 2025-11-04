# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import timedelta

import pytest
from flask import g


def _patch_break(monkeypatch, event, break_, payload):
    from indico.modules.events.timetable.controllers.manage import RHTimetableBreak

    monkeypatch.setattr('indico.web.args.IndicoFlaskParser.load_json', lambda *_: payload)
    g.rh = rh = RHTimetableBreak()
    rh.event = event
    rh.break_ = break_
    rh._process_PATCH()


def _patch_contrib(monkeypatch, event, contrib, payload):
    from indico.modules.events.timetable.controllers.manage import RHTimetableContribution

    monkeypatch.setattr('indico.web.args.IndicoFlaskParser.load_json', lambda *_: payload)
    g.rh = rh = RHTimetableContribution()
    rh.event = event
    rh.contrib = contrib
    rh._process_PATCH()


def _test_moves(
    patcher,
    obj,
    dummy_event,
    dummy_session,
    dummy_session_block,
    create_session,
    create_session_block,
    monkeypatch,
    change_time,
):
    # another block in the dummy session
    other_dummy_block = create_session_block(
        dummy_session, 'Dummy block 2', timedelta(minutes=20), dummy_event.start_dt
    )
    # a block in a different session
    other_session_block = create_session_block(
        create_session(dummy_event, 'other session'), 'Other block', timedelta(minutes=20), dummy_event.start_dt
    )
    start_dt_1 = obj.start_dt
    start_dt_2 = (obj.start_dt + timedelta(minutes=5)) if change_time else start_dt_1
    time_change_1 = {'start_dt': start_dt_1.isoformat()} if change_time else {}
    time_change_2 = {'start_dt': start_dt_2.isoformat()} if change_time else {}
    assert obj.start_dt == start_dt_1
    assert not obj.session_block
    # move top -> top
    patcher(monkeypatch, dummy_event, obj, time_change_2)
    assert obj.start_dt == start_dt_2
    assert not obj.session_block
    # move top -> block
    patcher(monkeypatch, dummy_event, obj, {'session_block_id': dummy_session_block.id, **time_change_1})
    assert obj.start_dt == start_dt_1
    assert obj.session_block == dummy_session_block
    # move inside block
    patcher(monkeypatch, dummy_event, obj, time_change_2)
    assert obj.start_dt == start_dt_2
    assert obj.session_block == dummy_session_block
    # move block -> different block in same session
    patcher(
        monkeypatch,
        dummy_event,
        obj,
        {'session_block_id': other_dummy_block.id, **time_change_1},
    )
    assert obj.start_dt == start_dt_1
    assert obj.session_block == other_dummy_block
    # move block -> different block in different session
    patcher(
        monkeypatch,
        dummy_event,
        obj,
        {'session_block_id': other_session_block.id, **time_change_2},
    )
    assert obj.start_dt == start_dt_2
    assert obj.session_block == other_session_block
    # move block -> top
    patcher(monkeypatch, dummy_event, obj, {'session_block_id': None, **time_change_1})
    assert obj.start_dt == start_dt_1
    assert not obj.session_block


@pytest.mark.usefixtures('request_context')
@pytest.mark.parametrize('change_time', (False, True))
def test_move_break(
    dummy_break,
    dummy_event,
    dummy_session,
    dummy_session_block,
    create_session,
    create_session_block,
    monkeypatch,
    change_time,
):
    _test_moves(
        _patch_break,
        dummy_break,
        dummy_event,
        dummy_session,
        dummy_session_block,
        create_session,
        create_session_block,
        monkeypatch,
        change_time,
    )


@pytest.mark.usefixtures('request_context')
@pytest.mark.parametrize('change_time', (False, True))
def test_move_contrib(
    dummy_event,
    dummy_contribution,
    dummy_session,
    dummy_session_block,
    create_session,
    create_session_block,
    create_timetable_entry,
    monkeypatch,
    change_time,
):
    create_timetable_entry(dummy_event, dummy_contribution, dummy_event.start_dt)
    _test_moves(
        _patch_contrib,
        dummy_contribution,
        dummy_event,
        dummy_session,
        dummy_session_block,
        create_session,
        create_session_block,
        monkeypatch,
        change_time,
    )

# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import timedelta

from indico.modules.events.models.events import EventType
from indico.modules.events.timetable.operations import schedule_contribution
from indico.util.date_time import now_utc

from .operations import delete_session, delete_session_block


def test_delete_session(dummy_session, dummy_session_block, dummy_contribution, request_context):
    dummy_contribution.session = dummy_session
    assert dummy_session.contributions
    assert dummy_session.blocks
    delete_session(dummy_session)
    assert dummy_session.is_deleted
    assert not dummy_session.blocks
    assert not dummy_session.contributions


def test_delete_session_block(dummy_session, dummy_session_block, dummy_contribution, request_context):
    schedule_contribution(dummy_contribution, now_utc(), dummy_session_block)
    delete_session_block(dummy_session_block)
    assert not dummy_session.blocks
    assert not dummy_session_block.timetable_entry
    assert not dummy_session_block.contributions
    assert dummy_session.is_deleted
    assert dummy_contribution.is_deleted


def test_delete_session_block_more_than_one(dummy_session, create_session_block, request_context):
    block_a = create_session_block(dummy_session, 'Block A', timedelta(minutes=20), now_utc())
    block_b = create_session_block(dummy_session, 'Block B', timedelta(minutes=20), now_utc())
    delete_session_block(block_a)
    assert not dummy_session.is_deleted
    delete_session_block(block_b)
    assert dummy_session.is_deleted


def test_delete_session_block_in_conference(dummy_session, dummy_session_block, dummy_contribution, request_context):
    dummy_session.event.type_ = EventType.conference
    schedule_contribution(dummy_contribution, now_utc(), dummy_session_block)
    delete_session_block(dummy_session_block)
    assert not dummy_contribution.is_deleted
    assert not dummy_contribution.timetable_entry


def test_delete_session_block_preserving_session(dummy_session, dummy_session_block, request_context):
    delete_session_block(dummy_session_block, delete_empty_session=False)
    assert not dummy_session.is_deleted

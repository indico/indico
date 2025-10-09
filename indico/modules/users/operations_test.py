# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.logs.models.entries import AppLogEntry, UserLogEntry
from indico.modules.users.operations import grant_admin, revoke_admin


def test_grant_admin(db, dummy_user, caplog):
    grant_admin(dummy_user, extra_log_data={'Context': 'Test'})
    db.session.flush()
    assert dummy_user.is_admin
    assert AppLogEntry.query.count() == 1
    app_log_entry = AppLogEntry.query.one()
    assert 'Admin privileges granted' in app_log_entry.summary
    assert app_log_entry.data['Context'] == 'Test'
    assert dummy_user.log_entries.count() == 1
    user_log_entry = UserLogEntry.query.one()
    assert 'Admin privileges granted' in user_log_entry.summary
    assert user_log_entry.data['Context'] == 'Test'
    assert len(caplog.records) == 1
    assert 'Admin rights granted' in caplog.text


def test_revoke_admin(db, dummy_user, caplog):
    dummy_user.is_admin = True
    revoke_admin(dummy_user, extra_log_data={'Context': 'Test'})
    db.session.flush()
    assert not dummy_user.is_admin
    assert AppLogEntry.query.count() == 1
    app_log_entry = AppLogEntry.query.one()
    assert 'Admin privileges revoked' in app_log_entry.summary
    assert app_log_entry.data['Context'] == 'Test'
    assert dummy_user.log_entries.count() == 1
    user_log_entry = UserLogEntry.query.one()
    assert 'Admin privileges revoked' in user_log_entry.summary
    assert user_log_entry.data['Context'] == 'Test'
    assert len(caplog.records) == 1
    assert 'Admin rights revoked' in caplog.text

# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest
from flask import Response

from indico.web.flask.session import IndicoSession, IndicoSessionInterface


def test_session_hard_expiry_dt_without_tz():
    """Test that passing an unaware datetime raises an error."""
    session = IndicoSession()

    with pytest.raises(ValueError):
        session.hard_expiry = datetime(2021, 1, 1, 0, 0, 0)


def test_get_storage_lifetime_with_hard_expiry(app, freeze_time):
    """Test the storage lifetime with hard expiry set on the session.

    The returned value should always be the minimum of the hard expiry and the
    app's permanent/temporary session lifetime.
    """
    dt_now = datetime.now(UTC)
    freeze_time(dt_now)
    session = IndicoSession()
    session.hard_expiry = dt_now + timedelta(days=2)
    session_interface = IndicoSessionInterface()

    # hard expiry shorter than permanent session lifetime
    session.permanent = True
    assert session_interface.get_storage_lifetime(app, session) == timedelta(days=2)

    # hard expiry longer than permanent session lifetime
    app.permanent_session_lifetime = timedelta(days=1)
    assert session_interface.get_storage_lifetime(
        app, session) == app.permanent_session_lifetime

    # hard expiry shorter than temporary session lifetime
    session.permanent = False
    assert session_interface.get_storage_lifetime(app, session) == timedelta(days=2)

    # hard expiry longer than temporary session lifetime
    session_interface.temporary_session_lifetime = timedelta(days=1)
    assert session_interface.get_storage_lifetime(
        app, session) == session_interface.temporary_session_lifetime


def test_save_session_with_hard_expiry(app):
    """Test that a session with a hard expiry sets the cookie expiry to the hard expiry."""
    session = IndicoSession()
    expiry = datetime.now(UTC) + timedelta(days=2)
    session.hard_expiry = expiry
    resp_mock = Mock(spec_set=Response)

    with app.test_request_context('/ping', method='GET'):
        IndicoSessionInterface().save_session(app, session, resp_mock)

    assert session.permanent
    resp_mock.set_cookie.assert_called_once()
    assert resp_mock.set_cookie.call_args[1].get('expires') == expiry

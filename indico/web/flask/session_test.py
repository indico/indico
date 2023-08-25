# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime, timedelta, timezone
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
    """Test that the storage lifetime is the hard expiry."""
    dt_now = datetime.now(timezone.utc)
    freeze_time(dt_now)
    session = IndicoSession()
    session.hard_expiry = dt_now + timedelta(days=2)

    assert IndicoSessionInterface().get_storage_lifetime(app, session) == timedelta(days=2)


def test_save_session_with_hard_expiry(app):
    """Test that a session with a hard expiry sets the cookie expiry to the hard expiry."""
    session = IndicoSession()
    expiry = datetime.now(timezone.utc) + timedelta(days=2)
    session.hard_expiry = expiry
    resp_mock = Mock(spec_set=Response)

    with app.test_request_context('/ping', method='GET'):
        IndicoSessionInterface().save_session(app, session, resp_mock)

    assert session.permanent
    resp_mock.set_cookie.assert_called_once()
    assert resp_mock.set_cookie.call_args[1].get('expires') == expiry

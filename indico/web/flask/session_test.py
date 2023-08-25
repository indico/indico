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


def test_get_storage_lifetime_with_hard_expiry(app, mocker):
    """Test that the storage lifetime is the hard expiry."""
    dt_mock = Mock(spec_set=datetime)
    dt_now = dt_mock.now.return_value = datetime.now(timezone.utc)
    mocker.patch('indico.web.flask.session.datetime', dt_mock)
    session = IndicoSession()
    session.hard_expiry = dt_now + timedelta(days=2)

    assert IndicoSessionInterface().get_storage_lifetime(app, session) == timedelta(days=2)


def test_should_refresh_session_with_hard_expiry(app):
    """Test that a session with a hard expiry should never be refreshed"""
    session = IndicoSession()
    session.hard_expiry = datetime.now(timezone.utc)

    assert not IndicoSessionInterface().should_refresh_session(app, session)


def test_save_session_with_hard_expiry(app):
    """Test that a session with a hard expiry sets the cookie expiry to the hard expiry."""
    session = IndicoSession()
    expiry = datetime.now(timezone.utc) + timedelta(days=2)
    session.hard_expiry = expiry
    resp_mock = Mock(spec_set=Response)

    with app.test_request_context(
        '/user/2/edit', method='POST', data={'name': ''}
    ):
        IndicoSessionInterface().save_session(app, session, resp_mock)

    assert session.permanent
    resp_mock.set_cookie.assert_called_once()
    assert resp_mock.set_cookie.call_args[1].get('expires') == expiry

# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import UTC, datetime

import pytest
from flask import session
from flask_multipass import IdentityInfo, InvalidCredentials, Multipass, NoSuchUser
from flask_multipass.providers.static import StaticIdentityProvider

from indico.modules.auth import process_identity
from indico.modules.auth.providers import IndicoAuthProvider


@pytest.mark.usefixtures('db')
def test_process_identity_sets_hard_expiry(app):
    """Test that hard expiry is set on the session object if it is present in the multipass data."""
    dt_now = datetime.now(UTC)
    identity_info = IdentityInfo(
        provider=StaticIdentityProvider(
            multipass=Multipass(), name='static', settings={}
        ),
        identifier='static', multipass_data={'session_expiry': dt_now}
    )

    with app.test_request_context('/ping', method='GET'):
        process_identity(identity_info)

        assert session.hard_expiry == dt_now


@pytest.mark.usefixtures('db')
def test_process_identity_raises_exc_for_non_dt_hard_expiry(app):
    """Test that a ValueError is raised if the hard expiry is not a datetime object."""
    identity_info = IdentityInfo(
        provider=StaticIdentityProvider(
            multipass=Multipass(), name='static', settings={}
        ),
        identifier='static', multipass_data={'session_expiry': 12345}
    )

    with app.test_request_context('/ping', method='GET'):
        with pytest.raises(ValueError):
            process_identity(identity_info)


@pytest.mark.parametrize(('user_id', 'email', 'secondary_email', 'identifier', 'password', 'login_data',
                          'expected_exc'), (
    ('1', 'user1@example.com', 'user11@example.com', 'user1', 'user1RealPassword',
     {'identifier': 'user1', 'password': 'user1RealPassword'}, None),
    ('2', 'user2@example.com', 'user22@example.com', 'user2', 'user2RealPassword',
     {'identifier': 'user2@example.com', 'password': 'user2RealPassword'}, None),
    ('3', 'user3@example.com', 'user33@example.com', 'user3', 'user3RealPassword',
     {'identifier': 'user33@example.com', 'password': 'user3RealPassword'}, None),
    ('4', 'user4@example.com', 'user44@example.com', 'user4', 'user4RealPassword',
     {'identifier': 'user4NoUser', 'password': 'user4RealPassword'}, NoSuchUser),
    ('5', 'user5@example.com', 'user55@example.com', 'user5', 'user5RealPassword',
     {'identifier': 'user5', 'password': 'user5WrongPassword'}, InvalidCredentials),
    ('6', 'user6@example.com', 'user66@example.com', 'user6', 'user6RealPassword',
     {'identifier': 'user6@example.com', 'password': 'user6WrongPassword'}, InvalidCredentials),
    ('7', 'user7@example.com', 'user77@example.com', 'user7', 'user7RealPassword',
     {'identifier': 'user77@example.com', 'password': 'user7WrongPassword'}, InvalidCredentials),
    ('8', 'user8@example.com', 'user88@example.com', 'user8', 'user8RealPassword',
     {'identifier': 'user888@example.com', 'password': 'user8RealPassword'}, NoSuchUser),
))
def test_process_local_login(app, mocker, create_user, create_identity, user_id, email, secondary_email, identifier,
                             password, login_data, expected_exc):
    multipass = mocker.MagicMock()
    settings = mocker.MagicMock()
    auth_provider = IndicoAuthProvider(multipass, 'Test provider', settings)

    user = create_user(user_id, email=email)
    user.secondary_emails.add(secondary_email)
    create_identity(user, 'Test provider', identifier, password=password)

    with app.test_request_context():
        if expected_exc:
            with pytest.raises(expected_exc):
                auth_provider.process_local_login(login_data)
        else:
            auth_provider.process_local_login(login_data)
            auth_provider.multipass.handle_auth_success.assert_called_once()


def test_process_local_login_with_same_identity_and_email(mocker, create_user, create_identity):
    multipass = mocker.MagicMock()
    settings = mocker.MagicMock()
    auth_provider = IndicoAuthProvider(multipass, 'Test provider', settings)

    user1 = create_user(21, email='dummy@example.com')
    user2 = create_user(23, email='mumu@example.com')

    create_identity(user1, 'Test provider', 'mumu@example.com', password='dummyUserPassword')
    create_identity(user2, 'Test provider', 'mumu', password='mumuUserPassword')

    auth_provider.process_local_login({'identifier': 'mumu@example.com', 'password': 'dummyUserPassword'})
    auth_info = multipass.handle_auth_success.call_args[0][0]
    assert auth_info.data['identity'].identifier == 'mumu@example.com'

    auth_provider.process_local_login({'identifier': 'mumu@example.com', 'password': 'mumuUserPassword'})
    auth_info = multipass.handle_auth_success.call_args[0][0]
    assert auth_info.data['identity'].identifier == 'mumu'

    with pytest.raises(InvalidCredentials):
        auth_provider.process_local_login({'identifier': 'mumu@example.com', 'password': 'NonePassword'})

# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import UTC, datetime

import pytest
from flask import session
from flask_multipass import IdentityInfo, Multipass
from flask_multipass.providers.static import StaticIdentityProvider

from indico.modules.auth import process_identity


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

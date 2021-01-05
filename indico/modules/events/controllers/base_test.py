# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from flask import session
from werkzeug.exceptions import Forbidden

from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.events.controllers.base import AccessKeyRequired, RHDisplayEventBase, RHProtectedEventBase


@pytest.mark.usefixtures('request_context')
def test_event_public_access(db, create_event):
    """Ensure if a null user can access a public event."""
    rh = RHProtectedEventBase()
    rh.event = create_event(1, protection_mode=ProtectionMode.public)
    rh._check_access()


@pytest.mark.usefixtures('request_context')
def test_event_protected_access(db, create_user, create_event):
    """
    Ensure a null user cannot access a protected event. Ensure a user
    with respective ACL entry can access a protected event.
    """
    rh = RHProtectedEventBase()
    rh.event = create_event(2, protection_mode=ProtectionMode.protected)
    with pytest.raises(Forbidden):
        rh._check_access()
    user = create_user(1)
    session.user = user
    with pytest.raises(Forbidden):
        rh._check_access()
    rh.event.update_principal(user, read_access=True)
    rh._check_access()


@pytest.mark.usefixtures('request_context')
def test_event_key_access(create_user, create_event):
    """
    Ensure the event doesn't reject the user if an access key is required.
    """
    rh = RHDisplayEventBase()
    rh.event = create_event(2, protection_mode=ProtectionMode.protected, access_key='abc')
    with pytest.raises(AccessKeyRequired):
        rh._check_access()

    user = create_user(1)
    rh.event.update_principal(user, read_access=True)
    session.user = user
    rh._check_access()

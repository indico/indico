# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.categories.util import can_create_unlisted_events
from indico.modules.events.settings import unlisted_events_settings


@pytest.mark.usefixtures('db')
def test_can_create_unlisted_events(dummy_user, create_user):
    admin_user = create_user(123, admin=True)
    assert not can_create_unlisted_events(None)
    unlisted_events_settings.set('enabled', False)
    unlisted_events_settings.set('restricted', False)
    assert not can_create_unlisted_events(dummy_user)
    assert not can_create_unlisted_events(admin_user)
    unlisted_events_settings.set('enabled', True)
    assert can_create_unlisted_events(dummy_user)
    unlisted_events_settings.set('restricted', True)
    assert not can_create_unlisted_events(dummy_user)
    unlisted_events_settings.acls.set('authorized_creators', {dummy_user})
    assert can_create_unlisted_events(dummy_user)
    assert can_create_unlisted_events(admin_user)

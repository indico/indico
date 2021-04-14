# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from unittest.mock import MagicMock

import pytest
from werkzeug.exceptions import Forbidden

from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.events.contributions.controllers.display import RHContributionDisplayBase, RHSubcontributionDisplay


@pytest.mark.usefixtures('request_context')
@pytest.mark.parametrize('event_allowed', (False, True))
@pytest.mark.parametrize('allowed', (False, True))
def test_contrib_explicit_access(dummy_event, dummy_user, allowed, event_allowed):
    dummy_event.protection_mode = ProtectionMode.public if event_allowed else ProtectionMode.protected
    rh = RHContributionDisplayBase()
    rh.event = dummy_event
    rh.contrib = MagicMock()
    rh.contrib.can_access.return_value = allowed
    # event access should not matter for the RH access check as having access e.g.
    # to a specific contribution lets users view the details for that contribution
    assert dummy_event.can_access(dummy_user) == event_allowed
    if allowed:
        rh._check_access()
    else:
        with pytest.raises(Forbidden):
            rh._check_access()


@pytest.mark.usefixtures('request_context')
@pytest.mark.parametrize('event_allowed', (False, True))
@pytest.mark.parametrize('allowed', (False, True))
def test_subcontrib_explicit_access(dummy_event, dummy_user, allowed, event_allowed):
    dummy_event.protection_mode = ProtectionMode.public if event_allowed else ProtectionMode.protected
    rh = RHSubcontributionDisplay()
    rh.event = dummy_event
    rh.subcontrib = MagicMock()
    rh.subcontrib.can_access.return_value = allowed
    # event access should not matter for the RH access check as having access e.g.
    # to a specific contribution lets users view the details for that subcontribution
    assert dummy_event.can_access(dummy_user) == event_allowed
    if allowed:
        rh._check_access()
    else:
        with pytest.raises(Forbidden):
            rh._check_access()

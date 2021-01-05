# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.cloning import EventCloner
from indico.modules.events.features.util import set_feature_enabled


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


@pytest.mark.usefixtures('dummy_reg')
def test_registration_clone(dummy_event, dummy_regform, create_event, dummy_user):
    set_feature_enabled(dummy_event, 'registration', True)

    assert dummy_regform.event == dummy_event
    assert dummy_event.registrations.one().user == dummy_user
    assert dummy_event.registrations.one().checked_in

    copied_event = create_event()
    EventCloner.run_cloners(dummy_event, copied_event, {'registrations', 'registration_forms'})
    copied_registration = copied_event.registrations.one()

    assert copied_registration.event == copied_event
    assert copied_registration.user == dummy_user
    assert not copied_registration.checked_in

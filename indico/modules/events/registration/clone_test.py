# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.cloning import EventCloner
from indico.modules.events.features.util import set_feature_enabled
from indico.modules.events.registration.models.tags import RegistrationTag


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


@pytest.mark.parametrize('has_tags', (False, True))
def test_registration_clone(dummy_event, dummy_regform, dummy_reg, create_event, dummy_user, has_tags):
    set_feature_enabled(dummy_event, 'registration', True)
    if has_tags:
        tag = RegistrationTag(title='Foo', color='b33f69', event=dummy_event)
        dummy_reg.tags = {tag}

    assert dummy_regform.event == dummy_event
    assert dummy_reg.user == dummy_user
    assert dummy_reg.checked_in

    copied_event = create_event()
    EventCloner.run_cloners(dummy_event, copied_event, {'registrations', 'registration_forms'})
    copied_registration = copied_event.registrations.one()

    assert copied_registration.event == copied_event
    assert copied_registration.user == dummy_user
    assert not copied_registration.checked_in
    if has_tags:
        assert tag not in copied_registration.tags
        assert copied_registration.tags == set(copied_event.registration_tags)
    else:
        assert not copied_registration.tags


@pytest.mark.usefixtures('dummy_regform')
def test_registration_tags_clone(dummy_event, create_event):
    set_feature_enabled(dummy_event, 'registration', True)
    tag = RegistrationTag(title='Foo', color='b33f69')
    dummy_event.registration_tags.append(tag)

    copied_event = create_event()
    EventCloner.run_cloners(dummy_event, copied_event, {'registration_forms'})

    assert len(copied_event.registration_tags) == 1
    copied_tag = copied_event.registration_tags[0]
    assert copied_tag != tag
    assert copied_tag.title == 'Foo'
    assert copied_tag.color == 'b33f69'

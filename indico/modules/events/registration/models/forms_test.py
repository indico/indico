# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core import signals
from indico.modules.events.registration.models.registrations import Registration, RegistrationState


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


def _add_registration(db, regform, email):
    reg = Registration(first_name='Test', last_name='User', email=email, currency='USD',
                       state=RegistrationState.complete, registration_form=regform)
    regform.event.registrations.append(reg)
    db.session.flush()
    return reg


def test_get_managed_registration_count_unscoped(db, dummy_regform, dummy_user):
    # With no scoping handler the full active count is returned.
    _add_registration(db, dummy_regform, 'a@example.test')
    _add_registration(db, dummy_regform, 'b@example.test')
    assert dummy_regform.get_managed_registration_count(dummy_user) == 2


def test_get_managed_registration_count_scoped(db, dummy_regform, dummy_user):
    # A handler returning a criterion scopes the count to the matching registrations.
    mine = _add_registration(db, dummy_regform, 'a@example.test')
    _add_registration(db, dummy_regform, 'b@example.test')

    def _scope(sender, user, **kwargs):
        return Registration.id == mine.id

    with signals.event.filter_registration_list.connected_to(_scope):
        assert dummy_regform.get_managed_registration_count(dummy_user) == 1

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
    _add_registration(db, dummy_regform, 'a@example.test')
    _add_registration(db, dummy_regform, 'b@example.test')
    assert dummy_regform.get_managed_registration_count(dummy_user) == 2


def test_get_managed_registration_count_scoped(db, dummy_regform, dummy_user):
    mine = _add_registration(db, dummy_regform, 'a@example.test')
    _add_registration(db, dummy_regform, 'b@example.test')

    def _scope(sender, user, **kwargs):
        return Registration.id == mine.id

    with signals.event.filter_registration_list.connected_to(_scope):
        assert dummy_regform.get_managed_registration_count(dummy_user) == 1


def test_get_managed_registration_count_include_inactive(db, dummy_regform, dummy_user):
    mine = _add_registration(db, dummy_regform, 'a@example.test')
    mine_withdrawn = _add_registration(db, dummy_regform, 'b@example.test')
    theirs_withdrawn = _add_registration(db, dummy_regform, 'c@example.test')
    mine_withdrawn.state = theirs_withdrawn.state = RegistrationState.withdrawn
    db.session.flush()

    def _scope(sender, user, **kwargs):
        return Registration.id.in_([mine.id, mine_withdrawn.id])

    assert dummy_regform.get_managed_registration_count(dummy_user, include_inactive=True) == 3
    with signals.event.filter_registration_list.connected_to(_scope):
        assert dummy_regform.get_managed_registration_count(dummy_user) == 1
        assert dummy_regform.get_managed_registration_count(dummy_user, include_inactive=True) == 2


def test_is_download_blocked(db, dummy_regform, dummy_user):
    assert dummy_regform.is_download_blocked(dummy_user) is False

    def _block(sender, user, **kwargs):
        return True

    with signals.event.is_registration_download_blocked.connected_to(_block):
        assert dummy_regform.is_download_blocked(dummy_user) is True

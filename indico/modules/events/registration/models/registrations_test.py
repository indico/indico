# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from types import SimpleNamespace

from indico.core import signals
from indico.modules.events.registration.models.registrations import Registration, RegistrationState


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


def _add_registration(db, regform, email):
    reg = Registration(first_name='Test', last_name='User', email=email, currency='USD',
                       state=RegistrationState.complete, registration_form=regform)
    regform.event.registrations.append(reg)
    db.session.flush()
    return reg


def test_can_manage_full_manager(db, dummy_regform, create_user):
    manager = create_user(2)
    dummy_regform.event.update_principal(manager, full_access=True)
    db.session.flush()
    reg = _add_registration(db, dummy_regform, 'a@example.test')
    assert reg.can_manage(manager, 'registration_edit')


def test_can_manage_scoped_grant_is_bounded(db, dummy_regform, create_user):
    manager = create_user(2)
    dummy_regform.event.update_principal(manager, permissions={'registration_edit'})
    db.session.flush()
    in_range = _add_registration(db, dummy_regform, 'in@example.test')
    out_range = _add_registration(db, dummy_regform, 'out@example.test')

    def _scope(sender, user, **kwargs):
        return Registration.id == in_range.id

    with signals.event.filter_registration_list.connected_to(_scope):
        assert in_range.can_manage(manager, 'registration_edit')
        assert not out_range.can_manage(manager, 'registration_edit')


def test_can_manage_denied_without_access(db, dummy_regform, create_user):
    reg = _add_registration(db, dummy_regform, 'a@example.test')
    assert not reg.can_manage(create_user(3), 'registration_edit')


def test_billable_data_sorted_by_form_order():
    section_a = SimpleNamespace(id=1, position=2)
    section_b = SimpleNamespace(id=2, position=1)

    def _data(name, section, position, field_id, price=10):
        field = SimpleNamespace(id=field_id, parent=section, position=position)
        return SimpleNamespace(name=name, price=price, field_data=SimpleNamespace(field=field))

    data = [
        _data('a2', section_a, 2, 10),
        _data('free', section_b, 3, 11, price=0),
        _data('b2', section_b, 2, 12),
        _data('a1', section_a, 1, 13),
        _data('b1', section_b, 1, 14),
    ]
    reg = SimpleNamespace(data=data)
    assert [x.name for x in Registration.billable_data.fget(reg)] == ['b1', 'b2', 'a1', 'a2']

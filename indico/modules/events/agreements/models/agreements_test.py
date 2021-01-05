# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from freezegun import freeze_time
from mock import MagicMock
from werkzeug.exceptions import ServiceUnavailable

from indico.modules.events.agreements.models.agreements import Agreement, AgreementState
from indico.util.date_time import now_utc


pytest_plugins = 'indico.modules.events.agreements.testing.fixtures'


@pytest.mark.parametrize(('state', 'expected'), (
    (AgreementState.pending, False),
    (AgreementState.accepted, True),
    (AgreementState.rejected, False),
    (AgreementState.accepted_on_behalf, True),
    (AgreementState.rejected_on_behalf, False),
))
def test_accepted(dummy_agreement, state, expected):
    dummy_agreement.state = state
    assert dummy_agreement.accepted == expected
    assert Agreement.find_one(accepted=expected) == dummy_agreement


@pytest.mark.parametrize(('state', 'expected'), (
    (AgreementState.pending, True),
    (AgreementState.accepted, False),
    (AgreementState.rejected, False),
    (AgreementState.accepted_on_behalf, False),
    (AgreementState.rejected_on_behalf, False),
))
def test_pending(dummy_agreement, state, expected):
    dummy_agreement.state = state
    filter_ = Agreement.pending if expected else ~Agreement.pending
    assert dummy_agreement.pending == expected
    assert Agreement.find_one(filter_) == dummy_agreement
    assert not Agreement.find_first(~filter_)


@pytest.mark.parametrize(('state', 'expected'), (
    (AgreementState.pending, False),
    (AgreementState.accepted, False),
    (AgreementState.rejected, True),
    (AgreementState.accepted_on_behalf, False),
    (AgreementState.rejected_on_behalf, True),
))
def test_rejected(dummy_agreement, state, expected):
    dummy_agreement.state = state
    assert dummy_agreement.rejected == expected
    assert Agreement.find_one(rejected=expected) == dummy_agreement


@pytest.mark.parametrize(('state', 'expected'), (
    (AgreementState.pending, False),
    (AgreementState.accepted, False),
    (AgreementState.rejected, False),
    (AgreementState.accepted_on_behalf, True),
    (AgreementState.rejected_on_behalf, True),
))
def test_signed_on_behalf(dummy_agreement, state, expected):
    dummy_agreement.state = state
    assert dummy_agreement.signed_on_behalf == expected
    assert Agreement.find_one(signed_on_behalf=expected) == dummy_agreement


def test_definition(mocker):
    from indico.modules.events.agreements import util
    mocker.patch.object(util, 'get_agreement_definitions', return_value={'foobar': 'test'})
    assert Agreement(type='foobar').definition == 'test'
    assert Agreement(type='barfoo').definition is None


def test_locator():
    id_ = 1337
    event_id = 9000
    agreement = Agreement(id=id_, event_id=event_id)
    assert agreement.locator == {'id': id_,
                                 'confId': event_id}


@pytest.mark.parametrize('person_with_user', (True, False))
def test_create_from_data(dummy_event, dummy_person, dummy_user, person_with_user):
    type_ = 'dummy'
    dummy_person.user = dummy_user if person_with_user else None
    agreement = Agreement.create_from_data(event=dummy_event, type_=type_, person=dummy_person)
    assert agreement.event == dummy_event
    assert agreement.type == type_
    assert agreement.state == AgreementState.pending
    assert agreement.uuid
    assert agreement.identifier == dummy_person.identifier
    assert agreement.person_email == dummy_person.email
    assert agreement.person_name == dummy_person.name
    assert agreement.user == dummy_person.user
    assert agreement.data == dummy_person.data


@freeze_time(now_utc())
@pytest.mark.usefixtures('mock_agreement_definition')
@pytest.mark.parametrize(('reason', 'on_behalf', 'expected_state'), (
    (None,     True,  AgreementState.accepted_on_behalf),
    (None,     False, AgreementState.accepted),
    ('reason', False, AgreementState.accepted),
))
def test_accept(reason, on_behalf, expected_state):
    ip = '127.0.0.1'
    agreement = Agreement()
    agreement.accept(from_ip=ip, reason=reason, on_behalf=on_behalf)
    assert agreement.state == expected_state
    assert agreement.signed_from_ip == ip
    assert agreement.reason == reason
    assert agreement.signed_dt == now_utc()
    agreement.definition.handle_accepted.assert_called_with(agreement)


@freeze_time(now_utc())
@pytest.mark.usefixtures('mock_agreement_definition')
@pytest.mark.parametrize(('reason', 'on_behalf', 'expected_state'), (
    (None,     True,  AgreementState.rejected_on_behalf),
    (None,     False, AgreementState.rejected),
    ('reason', False, AgreementState.rejected),
))
def test_reject(reason, on_behalf, expected_state):
    ip = '127.0.0.1'
    agreement = Agreement()
    agreement.reject(from_ip=ip, reason=reason, on_behalf=on_behalf)
    assert agreement.state == expected_state
    assert agreement.signed_from_ip == ip
    assert agreement.reason == reason
    assert agreement.signed_dt == now_utc()
    agreement.definition.handle_rejected.assert_called_with(agreement)


@pytest.mark.usefixtures('mock_agreement_definition')
def test_reset():
    agreement = Agreement()
    agreement.reset()
    assert agreement.state == AgreementState.pending
    assert agreement.attachment is None
    assert agreement.attachment_filename is None
    assert agreement.data is None
    assert agreement.reason is None
    assert agreement.signed_dt is None
    assert agreement.signed_from_ip is None


@pytest.mark.usefixtures('mock_agreement_definition')
def test_render():
    agreement = Agreement()
    agreement.render(None)
    agreement.definition.render_form.assert_called_with(agreement, None)


def test_render_no_definition(monkeypatch):
    monkeypatch.setattr(Agreement, 'definition', property(lambda s: None))
    agreement = Agreement()
    with pytest.raises(ServiceUnavailable):
        agreement.render(None)


def test_belongs_to():
    agreement = Agreement(identifier='foo')
    assert agreement.belongs_to(MagicMock(identifier='foo'))
    assert not agreement.belongs_to(MagicMock(identifier='bar'))


@pytest.mark.usefixtures('mock_agreement_definition')
def test_is_orphan(dummy_event):
    agreement = Agreement(event=dummy_event)
    agreement.is_orphan()
    agreement.definition.is_agreement_orphan(agreement.event, agreement)


def test_is_orphan_no_definition(monkeypatch):
    monkeypatch.setattr(Agreement, 'definition', property(lambda s: None))
    agreement = Agreement()
    with pytest.raises(ServiceUnavailable):
        agreement.is_orphan()

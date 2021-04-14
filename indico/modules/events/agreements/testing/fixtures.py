# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from uuid import uuid4

import pytest

from indico.modules.events.agreements.base import AgreementPersonInfo
from indico.modules.events.agreements.models.agreements import Agreement, AgreementState


@pytest.fixture
def create_person():
    """Return a callable which lets you create AgreementPersonInfo."""

    def _create_person(name, email, data=None):
        person = AgreementPersonInfo(name=name, email=email, data=data)
        return person

    return _create_person


@pytest.fixture
def create_agreement(db, dummy_event, dummy_person):
    """Return a a callable which lets you create agreements."""

    def _create_agreement(state):
        agreement = Agreement(uuid=str(uuid4()), event=dummy_event, type='dummy',
                              person_email=dummy_person.email, person_name=dummy_person.name, state=state,
                              identifier=dummy_person.identifier)
        db.session.add(agreement)
        db.session.flush()
        return agreement

    return _create_agreement


@pytest.fixture
def dummy_person(create_person):
    return create_person('dummy', 'dummy@test.com')


@pytest.fixture
def dummy_agreement(create_agreement):
    """Give you a dummy agreement with pending state."""
    return create_agreement(state=AgreementState.pending)


@pytest.fixture
def mock_agreement_definition(mocker):
    mocker.patch.object(Agreement, 'definition')

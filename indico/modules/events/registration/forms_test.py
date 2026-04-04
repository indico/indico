# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from types import SimpleNamespace

import pytest
from wtforms.validators import ValidationError

from indico.modules.events.registration.forms import TicketsForm


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


def test_reject_enabling_accompanying_person_tickets_when_anonymous_mode_is_active(
    dummy_regform, create_accompanying_persons_field
):
    create_accompanying_persons_field(0, False, is_anonymous=True)

    with pytest.raises(ValidationError) as exc_info:
        TicketsForm.validate_tickets_for_accompanying_persons(
            SimpleNamespace(regform=dummy_regform),
            SimpleNamespace(data=True),
        )

    assert str(exc_info.value) == ('Tickets for accompanying persons cannot be enabled because the registration '
                                    'form contains anonymous accompanying person registrations.')

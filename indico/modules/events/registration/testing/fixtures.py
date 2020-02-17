# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.util import create_personal_data_fields


@pytest.fixture
def dummy_regform(db, dummy_event):
    regform = RegistrationForm(event=dummy_event, title='Registration Form', currency='USD')
    create_personal_data_fields(regform)

    # enable all fields
    for field in regform.sections[0].fields:
        field.is_enabled = True
    db.session.add(regform)
    db.session.flush()
    return regform

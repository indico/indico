# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from marshmallow import ValidationError


def test_personal_data_schema(mocker):
    from indico.modules.users.schemas import UserPersonalDataSchema
    mocker.patch('indico.modules.users.schemas.user_management_settings.get')  # avoid db access
    schema = UserPersonalDataSchema(partial=True)
    assert schema.load({'first_name': 'Test'}) == {'first_name': 'Test'}
    # make sure the schema rejects user columns that should never be settable
    with pytest.raises(ValidationError):
        schema.load({'first_name': 'Test', 'is_admin': True})

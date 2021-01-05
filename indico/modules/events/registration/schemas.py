# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow.fields import String

from indico.core.marshmallow import mm
from indico.modules.events.registration.models.forms import RegistrationForm


class RegistrationFormPrincipalSchema(mm.ModelSchema):
    class Meta:
        model = RegistrationForm
        fields = ('id', 'name', 'identifier')

    name = String(attribute='title')
    identifier = String()

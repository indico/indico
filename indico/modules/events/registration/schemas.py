# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow.decorators import post_dump
from marshmallow.fields import String

from indico.core.marshmallow import mm
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.tags import RegistrationTag
from indico.util.string import natural_sort_key


class RegistrationFormPrincipalSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = RegistrationForm
        fields = ('id', 'name', 'identifier')

    name = String(attribute='title')
    identifier = String()


class RegistrationTagSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = RegistrationTag
        fields = ('id', 'title', 'color')

    @post_dump(pass_many=True)
    def sort_list(self, data, many, **kwargs):
        if many:
            data = sorted(data, key=lambda tag: natural_sort_key(tag['title']))
        return data

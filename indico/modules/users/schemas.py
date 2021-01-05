# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from marshmallow.fields import Function

from indico.core.marshmallow import mm
from indico.modules.users import User


class UserSchema(mm.ModelSchema):
    identifier = Function(lambda user: user.identifier)

    class Meta:
        model = User
        fields = ('id', 'identifier', 'first_name', 'last_name', 'email', 'affiliation', 'avatar_bg_color', 'full_name',
                  'phone')


user_schema = UserSchema()

# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow.fields import Function

from indico.core.marshmallow import mm
from indico.modules.categories import Category
from indico.modules.users import User


class UserSchema(mm.SQLAlchemyAutoSchema):
    identifier = Function(lambda user: user.identifier)

    class Meta:
        model = User
        fields = ('id', 'identifier', 'first_name', 'last_name', 'email', 'affiliation', 'full_name',
                  'phone', 'avatar_url')


class BasicCategorySchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Category
        fields = ('id', 'title', 'url', 'chain_titles')

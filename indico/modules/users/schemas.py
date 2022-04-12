# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow.fields import Function, List, String

from indico.core.marshmallow import mm
from indico.modules.categories import Category
from indico.modules.users import User
from indico.modules.users.models.users import UserTitle
from indico.util.marshmallow import NoneValueEnumField


class UserSchema(mm.SQLAlchemyAutoSchema):
    identifier = Function(lambda user: user.identifier)

    class Meta:
        model = User
        fields = ('id', 'identifier', 'first_name', 'last_name', 'email', 'affiliation', 'full_name',
                  'phone', 'avatar_url')


class UserPersonalDataSchema(mm.SQLAlchemyAutoSchema):
    title = NoneValueEnumField(UserTitle, none_value=UserTitle.none, attribute='_title')
    synced_fields = List(String())

    class Meta:
        model = User
        fields = ('title', 'first_name', 'last_name', 'email', 'affiliation', 'address', 'phone', 'synced_fields')


class BasicCategorySchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Category
        fields = ('id', 'title', 'url', 'chain_titles')

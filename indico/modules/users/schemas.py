# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pycountry
from marshmallow import fields, post_dump, post_load, pre_load, validate
from marshmallow.fields import Function, Integer, List, Method, Nested, String

from indico.core.marshmallow import mm
from indico.modules.categories import Category
from indico.modules.events import Event
from indico.modules.users import User
from indico.modules.users.models.affiliations import Affiliation
from indico.modules.users.models.users import UserTitle, syncable_fields
from indico.util.marshmallow import NoneValueEnumField


class UserSchema(mm.SQLAlchemyAutoSchema):
    identifier = Function(lambda user: user.identifier)

    class Meta:
        model = User
        fields = ('id', 'identifier', 'first_name', 'last_name', 'email', 'affiliation', 'full_name',
                  'phone', 'avatar_url')


class _AffiliationDataSchema(mm.Schema):
    affiliation_id = Integer(required=True, data_key='id', allow_none=True)
    name = String(required=True, data_key='text')


class UserPersonalDataSchema(mm.SQLAlchemyAutoSchema):
    title = NoneValueEnumField(UserTitle, none_value=UserTitle.none, attribute='_title')
    email = String(dump_only=True)
    synced_fields = List(String(validate=validate.OneOf(syncable_fields)))
    affiliation_data = Nested(_AffiliationDataSchema, attribute='_affiliation')

    class Meta:
        model = User
        # XXX: this schema is also used for updating a user's personal data, so the fields here must
        # under no circumstances include sensitive fields that should not be modifiable by a user!
        fields = ('title', 'first_name', 'last_name', 'email', 'affiliation', 'affiliation_data', 'address', 'phone',
                  'synced_fields')

    @pre_load
    def wrap_plain_affiliation(self, data, **kwargs):
        if (affiliation := data.pop('affiliation', None)) is not None:
            data['affiliation_data'] = {'id': None, 'text': affiliation}
        return data

    @post_dump
    def sort_synced_fields(self, data, **kwargs):
        data['synced_fields'].sort()
        return data

    @post_load
    def fix_key(self, data, **kwargs):
        if affiliation := data.pop('_affiliation', None):
            data['affiliation_data'] = affiliation
        return data


class BasicCategorySchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Category
        fields = ('id', 'title', 'url', 'chain_titles')


class FavoriteEventSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Event
        fields = ('id', 'title', 'label_markup', 'url', 'location', 'chain_titles', 'start_dt', 'end_dt')

    location = fields.String(attribute='event.location.venue_name')
    chain_titles = fields.List(fields.String(), attribute='category.chain_titles')
    label_markup = fields.Function(lambda e: e.get_label_markup('mini'))


class AffiliationSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Affiliation
        fields = ('id', 'name', 'street', 'postcode', 'city', 'country_code', 'country_name', 'meta')

    country_name = Method('get_country_name')

    def get_country_name(self, obj):
        if country := pycountry.countries.get(alpha_2=obj.country_code):
            return country.name
        else:
            return ''

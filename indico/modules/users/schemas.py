# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import fields, post_dump, post_load, validate
from marshmallow.fields import List, String

from indico.core.marshmallow import mm
from indico.modules.categories.models.categories import Category
from indico.modules.events import Event
from indico.modules.users import User
from indico.modules.users.models.affiliations import Affiliation
from indico.modules.users.models.users import UserTitle, syncable_fields
from indico.util.countries import get_country
from indico.util.marshmallow import ModelField, NoneValueEnumField


class AffiliationSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Affiliation
        fields = ('id', 'name', 'street', 'postcode', 'city', 'country_code', 'meta')

    @post_dump
    def add_country_name(self, data, **kwargs):
        data['country_name'] = get_country(data['country_code']) or ''
        return data


class BasicAffiliationSchema(AffiliationSchema):
    """
    A schema containing basic information about a predefined affiliation that
    is intended to be used in exports.
    """

    class Meta(AffiliationSchema.Meta):
        fields = ('id', 'name', 'street', 'postcode', 'city', 'country_code')


class UserSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        fields = ('id', 'identifier', 'first_name', 'last_name', 'email', 'affiliation', 'affiliation_id',
                  'title', 'affiliation_meta', 'full_name', 'phone', 'avatar_url')

    affiliation_id = fields.Integer(load_default=None, dump_only=True)
    affiliation_meta = fields.Nested(AffiliationSchema, attribute='affiliation_link', dump_only=True)
    title = NoneValueEnumField(UserTitle, none_value=UserTitle.none, attribute='_title')


class BasicUserSchema(UserSchema):
    """
    A schema containing basic information about the user that can be safely
    exposed to event organizers.
    """

    affiliation_meta = fields.Nested(BasicAffiliationSchema, attribute='affiliation_link', dump_only=True)

    class Meta(UserSchema.Meta):
        fields = ('id', 'identifier', 'first_name', 'last_name', 'email', 'affiliation', 'affiliation_meta',
                  'full_name', 'title', 'avatar_url')


class UserPersonalDataSchema(mm.SQLAlchemyAutoSchema):
    title = NoneValueEnumField(UserTitle, none_value=UserTitle.none, attribute='_title')
    email = String(dump_only=True)
    synced_fields = List(String(validate=validate.OneOf(syncable_fields)))
    affiliation_link = ModelField(Affiliation, data_key='affiliation_id', load_default=None, load_only=True)
    affiliation_data = fields.Function(lambda u: {'id': u.affiliation_id, 'text': u.affiliation}, dump_only=True)

    class Meta:
        model = User
        # XXX: this schema is also used for updating a user's personal data, so the fields here must
        # under no circumstances include sensitive fields that should not be modifiable by a user!
        fields = ('title', 'first_name', 'last_name', 'email', 'address', 'phone', 'synced_fields',
                  'affiliation', 'affiliation_data', 'affiliation_link')

    @post_dump
    def sort_synced_fields(self, data, **kwargs):
        data['synced_fields'].sort()
        return data

    @post_load
    def ensure_affiliation_text(self, data, **kwargs):
        if affiliation_link := data.get('affiliation_link'):
            data['affiliation'] = affiliation_link.name
        elif 'affiliation' in data:
            # clear link if we update only the affiliation text for some reason
            data['affiliation_link'] = None
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

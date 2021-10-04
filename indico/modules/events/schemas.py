# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import EXCLUDE, fields

from indico.core.marshmallow import mm
from indico.modules.events.models.events import Event
from indico.modules.events.models.principals import EventPrincipal
from indico.modules.users.models.users import UserTitle
from indico.util.i18n import orig_string
from indico.util.marshmallow import PrincipalPermissionList


class EventPermissionsSchema(mm.Schema):
    acl_entries = PrincipalPermissionList(EventPrincipal, all_permissions=True)


class EventDetailsSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Event
        fields = ('id', 'category_chain', 'title', 'start_dt', 'end_dt')

    category_chain = fields.List(fields.String(), attribute='category.chain_titles')


# TODO: move to /persons
class PersonLinkSchema(mm.Schema):
    class Meta:
        unknown = EXCLUDE

    _type = fields.Constant('PersonLink')
    title = fields.Method('get_title', deserialize='load_title')
    first_name = fields.String(missing='')
    last_name = fields.String(required=True)
    affiliation = fields.String(missing='')
    phone = fields.String(missing='')
    address = fields.String(missing='')
    email = fields.String(required=True)
    display_order = fields.Int()
    user_id = fields.Function(lambda o: o.person.user_id)
    name = fields.String(data_key='display_full_name')
    avatar_url = fields.Function(lambda o: o.person.user.avatar_url)

    def get_title(self, obj):
        return obj.title

    def load_title(self, title):
        return next((x.value for x in UserTitle if title == orig_string(x.title)), UserTitle.none)


event_permissions_schema = EventPermissionsSchema()
